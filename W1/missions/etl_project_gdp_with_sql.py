import re
import sqlite3
from datetime import datetime
import requests
from bs4 import BeautifulSoup
import pandas as pd
import country_converter as coco
import logging
logging.getLogger("country_converter").setLevel(logging.ERROR)  # 매칭 오류 메시지 숨김

URL = "https://en.wikipedia.org/wiki/List_of_countries_by_GDP_(nominal)"
HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
DB_PATH = "World_Economies.db"
TABLE_NAME = "Countries_by_GDP"

# country_converter 인스턴스 (모듈 최초 로드 시 1회 생성 -> 반복 호출 비용 절감)
cc = coco.CountryConverter()


def log_progress(message):
    # 로그 파일 "etl_project_log.txt"에 기록하는 함수
    timestamp_format = "%Y-%B-%d-%H-%M-%S"
    now = datetime.now().strftime(timestamp_format)
    with open("etl_project_log.txt", "a", encoding="utf-8") as f:
        f.write(f"{now}, {message}\n")


# ------ Extract ------
def extract_main_table(url):
    # Wikipedia 사이트 속 IMF에서 제공하는 국가별 GDP가 있는 테이블 데이터 추출하는 함수
    response = requests.get(url, headers=HEADERS)
    response.raise_for_status()

    soup = BeautifulSoup(response.text, "html.parser")

    for caption in soup.find_all("caption"):
        caption_text = caption.get_text(strip=True)
        if "GDP forecast" in caption_text and "by country" in caption_text.lower():
            return caption.find_parent("table")

    raise ValueError(
        "국가별 GDP 테이블을 찾지 못했습니다. Wikipedia 페이지 구조나 캡션 문구가 변경되었을 수 있습니다."
    )


def parse_table_to_records(table):
    # Raw 데이터를 담아 둔 리스트 반환
    rows = []
    for tr in table.find_all("tr"):
        cells = tr.find_all(["th", "td"])
        for cell in cells:
            for sup in cell.find_all("sup"):
                sup.decompose()
        row = [cell.get_text(strip=True) for cell in cells]
        if row:
            rows.append(row)

    columns = rows[0]
    data_rows = rows[1:]
    records = [dict(zip(columns, row)) for row in data_rows]
    return records


def extract():
    log_progress("Extract phase Started")

    table = extract_main_table(URL)
    records = parse_table_to_records(table)

    # 국가명을 한 번에 리스트로 모아서 단 1번만 cc.convert() 호출
    country_names = [record.get("Country/Territory", "") for record in records]
    regions = cc.convert(names=country_names, to="continent", not_found=None)

    for record, region in zip(records, regions):
        record["Region"] = region

    log_progress("Extract phase Ended")
    return records


# 테이블 안의 데이터를 숫자로 변환 함수
def clean_gdp_value(val):
    if val is None or "N/a" in str(val):
        return None
    val = re.sub(r"\(.*?\)", "", str(val))  # 괄호 안 내용 제거
    val = val.replace(",", "").strip()
    return pd.to_numeric(val, errors="coerce")


# ----- Transform -----
def transform(records: list) -> pd.DataFrame:

    log_progress("Transform phase Started")

    df = pd.DataFrame(records)  # 리스트 내의 딕셔너리로 저장된 데이터 - 데이터프레임으로 변환

    imf_col = next(  # IMF 조사연도가 바뀌더라도 상관 없음 - 재사용 가능
        (c for c in df.columns if c.upper().startswith("IMF")), None
    )

    if imf_col is None:
        log_progress("Transform phase Failed - IMF column not found")
        raise ValueError("IMF 컬럼을 찾지 못했습니다. 컬럼명 패턴이 바뀌었을 수 있습니다.")

    df[imf_col] = df[imf_col].apply(clean_gdp_value)

    # 'World' 국가별 합계 행은 제외
    df = df[df["Country/Territory"] != "World"].copy()
    # 테이블 기본 단위 million를 billion으로 변환, 소수점 2번째 자리까지 반올림
    df["GDP_USD_billion"] = (df[imf_col] / 1000).round(2)
    df = df.dropna(subset=["GDP_USD_billion"])
    # GDP 순으로 정렬
    df = df.sort_values("GDP_USD_billion", ascending=False).reset_index(drop=True)

    # 컬럼명을 최종 스키마 기준(Country, GDP_USD_billion)으로 정리
    df = df.rename(columns={"Country/Territory": "Country"})
    result_df = df[["Country", "Region", "GDP_USD_billion"]]

    log_progress("Transform phase Ended")
    return result_df


# ----- Load -----
# DB에 저장
def save_to_db(df, db_path, table_name):
    log_progress("Load to Database Started")

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    cursor.execute(f"DROP TABLE IF EXISTS {table_name}")
    cursor.execute(f"""
        CREATE TABLE {table_name} (
            Country TEXT,
            Region TEXT,
            GDP_USD_billion REAL
        )
    """)

    rows = list(df[["Country", "Region", "GDP_USD_billion"]].itertuples(index=False, name=None))
    cursor.executemany(
        f"INSERT INTO {table_name} (Country, Region, GDP_USD_billion) VALUES (?, ?, ?)",
        rows
    )

    conn.commit()
    cursor.close()

    log_progress("Load to Database Ended")
    return conn


# SQL 쿼리 실행 및 출력
def run_query(query_statement, sql_connection):
    log_progress(f"Query Started: {query_statement.strip()}")

    cursor = sql_connection.cursor()
    cursor.execute(query_statement)
    rows = cursor.fetchall()
    columns = [description[0] for description in cursor.description]

    # 출력 (이쁘게)
    header = " | ".join(columns)
    print(header)
    print("-" * len(header))

    for row in rows:
        print(" | ".join(str(value) for value in row))

    cursor.close()
    log_progress("Query Ended")


def load_and_display(sql_connection, table_name):
    log_progress("Load phase Started")

    # 1) GDP >= 100B USD 국가만 SQL로 조회
    query_high_gdp = f"""
        SELECT Country, Region, GDP_USD_billion
        FROM {table_name}
        WHERE GDP_USD_billion >= 100
        ORDER BY GDP_USD_billion DESC
    """
    run_query(query_high_gdp, sql_connection)

    # 2) Region별 top5 국가 GDP 평균을 SQL 윈도우 함수로 조회
    query_region_top5_avg = f"""
        WITH ranked AS (
            SELECT Country, Region, GDP_USD_billion,
                   ROW_NUMBER() OVER (
                       PARTITION BY Region ORDER BY GDP_USD_billion DESC
                   ) AS rn
            FROM {table_name}
            WHERE Region IS NOT NULL
        )
        SELECT Region, ROUND(AVG(GDP_USD_billion), 2) AS GDP_USD_billion
        FROM ranked
        WHERE rn <= 5
        GROUP BY Region
        ORDER BY GDP_USD_billion DESC
    """
    run_query(query_region_top5_avg, sql_connection)

    log_progress("Load phase Ended")


# ----- ETL 파이프라인 -----
def etl_pipeline():
    log_progress("ETL Job Started")

    raw_records = extract()
    df = transform(raw_records)

    conn = save_to_db(df, DB_PATH, TABLE_NAME)
    load_and_display(conn, TABLE_NAME)
    conn.close()

    log_progress("ETL Job Ended")
    return df


if __name__ == "__main__":
    final_df = etl_pipeline()