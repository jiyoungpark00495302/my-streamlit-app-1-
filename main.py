from fastapi import FastAPI
from pydantic import BaseModel
from typing import Literal
import openai
import json
import re
import random

# ✅ OpenAI 클라이언트
client = openai.Client(api_key="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")

app = FastAPI()

@app.get("/")
def root():
    return {
        "message": "✅ FastAPI 서버 실행 중입니다. '/docs'에서 API 문서를 확인하거나 '/recommend' 엔드포인트를 사용하세요."
    }

class StudentInfo(BaseModel):
    student_id: str
    grade: int
    remarks: str
    attendance: str
    career: str
    question_freq: Literal["상", "중", "하"]
    assignment_attitude: Literal["우수", "보통", "낮음"]
    self_awareness: bool

valid_priorities = {"개념적", "정서적", "전략적", "메타인지적"}

# ✅ 자동 우선순위 추론 규칙 함수
def infer_priorities(info: dict) -> list:
    reasons = []

    if not info['self_awareness']:
        p1 = "메타인지적"
        reasons.append("학생이 자신의 학습 문제를 인식하지 못함")
    elif info['grade'] >= 5:
        p1 = "개념적"
        reasons.append("성적이 낮아 개념적 개입이 필요함")
    elif info['assignment_attitude'] == "낮음" or info['question_freq'] == "하":
        p1 = "전략적"
        reasons.append("학습 수행 태도나 질문 빈도가 낮아 전략적 개입이 필요함")
    elif re.search(r"(소극|무기력|불안|자신감 없음)", info['remarks']):
        p1 = "정서적"
        reasons.append("세부사항에서 정서적 문제가 감지됨")
    else:
        p1 = random.choice(list(valid_priorities))
        reasons.append("명확한 요인이 없어 무작위 선택")

    remaining = list(valid_priorities - {p1})
    p2 = random.choice(remaining)
    reasons.append(f"{p1}을 보완하기 위한 보조적 개입으로 {p2} 선택")

    return [p1, p2, " / ".join(reasons)]

# ✅ GPT 처리 함수
def recommend_scaffolding_gpt(student_info: dict) -> dict:
    try:
        prompt = f"""당신은 고등학교 3학년 수학 교사를 돕는 AI입니다.

다음은 학생의 정보입니다:
- 성적 등급: {student_info['grade']}등급
- 세부능력특기사항: {student_info['remarks']}
- 출결 정보: {student_info['attendance']}
- 진로 희망 사항: {student_info['career']}
- 수업 중 질문 빈도: {student_info['question_freq']}
- 과제 및 수행평가 성실도: {student_info['assignment_attitude']}
- 스스로 문제 인식 여부: {"있음" if student_info['self_awareness'] else "없음"}

이 학생에게 추천할 스캐폴딩 정보를 다음 JSON 형식으로 정확하게 출력하세요.
priority_1과 priority_2는 반드시 ["개념적", "정서적", "전략적", "메타인지적"] 중 하나씩 사용하세요. 설명은 하지 마세요.

{{
  "student_id": "{student_info['student_id']}",
  "priority_1": "...",
  "priority_2": "...",
  "reason": "...",
  "strategies": {{
    "priority_1": "...",
    "priority_2": "..."
  }}
}}"""

        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "당신은 교육 전문가이자 GPT 기반 스캐폴딩 분석 시스템입니다."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3
        )

        content = response.choices[0].message.content.strip()

        parsed = None
        try:
            parsed = json.loads(content)
        except json.JSONDecodeError:
            match = re.search(r'\{[\s\S]*\}', content)
            if match:
                try:
                    parsed = json.loads(match.group())
                except json.JSONDecodeError:
                    parsed = None

        if parsed and parsed.get("priority_1") in valid_priorities and parsed.get("priority_2") in valid_priorities:
            return parsed
        else:
            p1, p2, reason = infer_priorities(student_info)
            return {
                "student_id": student_info['student_id'],
                "priority_1": p1,
                "priority_2": p2,
                "reason": reason,
                "strategies": {
                    "priority_1": f"{p1} 스캐폴딩 전략 예시입니다. 개별 지도에 따라 구체화 필요.",
                    "priority_2": f"{p2} 스캐폴딩 전략 예시입니다. 개별 지도에 따라 구체화 필요."
                },
                "note": "GPT 응답이 유효하지 않아 규칙 기반으로 자동 생성됨"
            }

    except Exception as e:
        return {"error": str(e)}

@app.get("/recommend")
def recommend_get(
    student_id: str,
    grade: int,
    remarks: str,
    attendance: str,
    career: str,
    question_freq: Literal["상", "중", "하"],
    assignment_attitude: Literal["우수", "보통", "낮음"],
    self_awareness: bool
):
    student_info = {
        "student_id": student_id,
        "grade": grade,
        "remarks": remarks,
        "attendance": attendance,
        "career": career,
        "question_freq": question_freq,
        "assignment_attitude": assignment_attitude,
        "self_awareness": self_awareness
    }
    return recommend_scaffolding_gpt(student_info)

@app.post("/recommend")
def recommend_post(info: StudentInfo):
    return recommend_scaffolding_gpt(info.dict())
