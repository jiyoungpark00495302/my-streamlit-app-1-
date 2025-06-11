import os

def create_env_file():
    key = input("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").strip()

    if not key.startswith("sk-"):
        print("❌ 올바른 OpenAI API 키 형식이 아닙니다.")
        return

    env_path = os.path.join(os.getcwd(), ".env")
    
    with open(env_path, "w") as f:
        f.write(f"OPENAI_API_KEY={key}\n")
    
    print(f"✅ .env 파일이 다음 경로에 생성되었습니다: {env_path}")

if __name__ == "__main__":
    create_env_file()
