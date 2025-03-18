"""
簡單測試 Azure OpenAI 服務是否正常運作
支持交互式對話，輸入 'Exit' 結束對話
"""

from app.ai_services.openai_service import OpenAIService
import json

def print_response(response_json: str):
    """格式化輸出 AI 回應"""
    try:
        # 嘗試解析並格式化 JSON 響應
        response = json.loads(response_json)
        print("\n🤖 AI 分析結果:")
        print("------------------------")
        
        # 識別出的症狀
        print("📋 識別的症狀:")
        for symptom in response.get("identified_symptoms", []):
            print(f"  • {symptom}")
        
        # 嚴重程度評估
        print(f"\n⚠️ 嚴重程度評估:")
        print(f"  {response.get('severity_assessment', '無評估')}")
        
        # 建議
        print("\n💡 建議:")
        for rec in response.get("recommendations", []):
            print(f"  • {rec}")
        
        # 追問問題
        print("\n❓ 追問問題:")
        for question in response.get("follow_up_questions", []):
            print(f"  • {question}")
            
        print("------------------------")
    except json.JSONDecodeError:
        # 如果不是有效的 JSON，直接輸出原始內容
        print("\n🤖 AI 回應:")
        print("------------------------")
        print(response_json)
        print("------------------------")

def main():
    try:
        # 初始化服務
        service = OpenAIService()
        print("✓ 服務初始化成功")
        print("\n🤖 您好！我是您的智能問診助手。請描述您的症狀，我會協助您進行分析。")
        print("（輸入 'Exit' 結束對話）")
        
        while True:
            # 獲取用戶輸入
            user_input = input("\n👤 請描述您的症狀: ")
            
            # 檢查是否要退出
            if user_input.lower() == 'exit':
                print("\n👋 感謝使用，再見！")
                break
            
            # 調用服務
            result = service.analyze_symptoms(user_input)
            
            # 輸出結果
            print_response(result)
            
    except Exception as e:
        print(f"\n❌ 錯誤: {str(e)}")
        raise

if __name__ == "__main__":
    main() 