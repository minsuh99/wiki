# 개념 정리

컨테이너 
- 프로그램 + 프로그램이 필요한 환경(OS, 라이브러리, 설정)을 하나로 패키징해 묶어놓은 것. 어디에서 누가 사용해도 그 환경 안에서 항상 똑같이 재현되게 만듬

Docker 
- 그러한 컨테이너를 만들고 관리하는 프로그램, 도구. 

이미지 
- 어떤 개발 환경을 만들 것인지에 대해 기술해놓은 파일. 이를 빌드하면 그 환경을 바탕으로 만들어진 컨테이너

레지스터리 (ECR / Docker Hub)
- 만든 이미지를 저장해서 다른 컴퓨터가 받아갈 수 있게 하는 중앙 창고
- 로컬 → push → 레지스트리 → pull → EC2 순서로 이미지가 이동

IAM 사용자 vs IAM Role
- IAM 사용자는 "사람"에게 부여하는 권한
- IAM Role은 "EC2 인스턴스 같은 리소스 자체"에 부여하는 권한

user-data.sh
- EC2 인스턴스가 최초 부팅될 때 딱 한 번만 자동으로 실행되는 초기화 스크립트
- 매번 SSH로 들어가서 설정할 필요 없이, 인스턴스가 뜨자마자 Docker 설치와 이미지 pull/run까지 자동으로 처리되게 만드는 "재현 가능한 배포"의 핵심


# 터미널에 쓰는 명령어

## 이미지 빌드
```
docker build --platform <아키텍처> -t <이미지명> . 
```
## 테스팅
```
docker run -p <호스트포트>:<컨테이너포트> <이미지명>
```
## 컨테이너&이미지 관리 명령어
```docker images # 이미지 목록
docker ps # 실행 중인 컨테이너
docker ps -a # 전체 컨테이너(멈춘 것 포함)

docker stop <컨테이너ID>
docker rm <컨테이너ID>
docker rmi <이미지ID>

docker container prune # 멈춘 컨테이너 일괄 정리
docker image prune # 태그 없는 이미지 일괄 정리
```

## 레지스터리 태그 & 로그인 & push
```
docker tag <로컬이미지명>:<태그> <레지스트리주소>/<리포지토리명>:<태그>

<레지스트리인증명령어> | docker login --username <사용자명> --password-stdin <레지스트리주소>

docker push <레지스트리주소>/<리포지토리명>:<태그>
```

## 원격 서버에서 사용할 때
```
ssh -i <키파일> <사용자>@<서버주소> # 접속

docker pull <레지스트리주소>/<리포지토리명>:<태그>
docker stop <컨테이너명> 2>/dev/null
docker rm <컨테이너명> 2>/dev/null
docker run -d -p <호스트포트>:<컨테이너포트> --name <컨테이너명> --restart always \
  <레지스트리주소>/<리포지토리명>:<태그>
```

## MFA 활용?
```
<임시인증명령어> --serial-number <MFA기기ID> --token-code <인증코드>

export <액세스키환경변수>=<값>
export <시크릿키환경변수>=<값>
export <세션토큰환경변수>=<값>
```