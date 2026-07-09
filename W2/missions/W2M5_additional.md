# W2M5 - 추가학습거리
- 논문 Summary를 읽고 소감을 위키에 기술
- 논문: [Yadala, Sucharitha & Vijayalata, Y. & Prasad, V.. (2020). Predicting Election Results from Twitter Using Machine Learning Algorithms. Recent Advances in Computer Science and Communications. 13. 10.2174/2666255813999200729164142.](http://www.cse.griet.ac.in/pdfs/journals20-21/SC17.pdf)

## 초록
- 소셜미디어, 특히 트위터 속 사용자들의 자유로운 정치적 견해에 대한 표현에 주목해 이를 분석하면 선거 결과를 예측할 수 있다고 생각함
- 기존에 여론조사 기관이나 전문가를 통한 예측의 방식에서 트위터 속 선거에 출마한 후보자나 정당 관련 트윗을 수집하고 이를 _감정분석_ 을 통해 긍정과 부정으로 분류하며 지지도로 환산하여 결과 예측에 활용
- SVM(Support Vector Machine) 분류기를 15-fold 교차검증으로 학습 -> 정확도 94.2%를 달성
- 학습 데이터: 총 7,500개 트윗 (긍정 3,750 + 부정 3,750, 균형 잡힌 데이터셋)
- PSS(Public Sentiment Score)를 통해 1, 2, 3위 정당의 의석 수를 예측
- 실험 결과가 실제 선거 결과와 매우 유사하며, 기존 조사 기관의 방식과 비교했을 때 SNS 데이터가 더 높은 정확도로 결과를 예측할 수 있음을 입증했다는 설명

## 개인적 견해
- SNS 데이터만으로는 선거 결과를 예측하는 데에 큰 의미가 있을까?라는 생각이 먼저 들었다.
- 여론조사와 같은 기존 조사 기관 방식보다 예측력이 좋다면 선거 비용을 아예 줄이거나 이와 결합한 새로운 지표를 선거 예측의 보조자료로 활용한다면 의미가 있을 것 같다.
