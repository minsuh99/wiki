import json
import re
from datetime import datetime
import requests
from bs4 import BeautifulSoup
import pandas as pd
import country_converter as coco
import logging
logging.getLogger("country_converter").setLevel(logging.ERROR)# 매칭 오류 메시지 숨김

URL = "https://en.wikipedia.org/wiki/List_of_countries_by_GDP_(nominal)"
HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}

# country_converter 인스턴스 (모듈 최초 로드 시 1회 생성 -> 반복 호출 비용 절감)
cc = coco.CountryConverter()


def log_progress(message):
    # 로그 파일 "etl_project_log.txt"에 기록하는 함수
    timestamp_format = "%Y-%B-%d-%H-%M-%S"
    now = datetime.now().strftime(timestamp_format)
    with open("etl_project_log.txt", "a", encoding="utf-8") as f:
        f.write(f"{now}, {message}\n")


# Extract 함수
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
    # Raw 데이터를 json에 저장하기 위한 딕셔너리를 담아 둔 리스트 반환
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


def get_region(country_name):
    # country_converter로 국가명을 대륙으로 변환
    return cc.convert(names=country_name, to="continent", not_found=None)


def load_from_json(path: str):
    """JSON 파일에서 raw 데이터를 로드 (재실행 시 스크래핑 없이 재사용 가능)."""
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


# ------ Extract ------
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
def transform(records):

    log_progress("Transform phase Started")

    df = pd.DataFrame(records)  # 리스트 내의 딕셔너리로 저장된 json 데이터 - 데이터프레임으로 변환

    imf_col = next( # IMF 조사연도가 바뀌더라도 상관 없음 - 재사용 가능
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
# JSON 파일에 저장한 파일로 필터링한 결과 출력
def load_and_display(df):
    log_progress("Load phase Started")

    high_gdp_df = df[df["GDP_USD_billion"] >= 100]
    print(f"\n=== GDP >= 100B USD 국가 ===")
    print(high_gdp_df.to_string(index=False))

    region_avg_df = (
        df.dropna(subset=["Region"])
        .groupby("Region")
        .apply(lambda g: g.nlargest(5, "GDP_USD_billion")["GDP_USD_billion"].mean())
        .round(2)
        .reset_index(name="Top5_Avg_GDP_USD_billion")
        .sort_values("Top5_Avg_GDP_USD_billion", ascending=False)
    )
    print(f"\n=== Region별 Top 5 국가 GDP 평균 (GDP_USD_billion) ===")
    print(region_avg_df.to_string(index=False))

    log_progress("Load phase Ended")


# Load된 결과 저장
def save_to_json(records: list, path: str) -> None:
    log_progress("Save final data to JSON Started")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(records, f, ensure_ascii=False, indent=2)
    log_progress("Save final data to JSON Ended")


# ETL 파이프라인
def etl_pipeline():
    log_progress("ETL Job Started")

    raw_records = extract()
    df = transform(raw_records)

    # 최종(Transform 완료) 데이터를 JSON으로 저장 (Extract 직후 raw 데이터가 아님)
    save_to_json(df.to_dict(orient="records"), "Countries_by_GDP.json")

    load_and_display(df)

    log_progress("ETL Job Ended")
    return df


if __name__ == "__main__":
    final_df = etl_pipeline()