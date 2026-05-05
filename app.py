import os
import requests
from flask import Flask, send_file, jsonify, request
import openpyxl
from collections import Counter
from datetime import datetime

app = Flask(__name__, static_folder='static')

# 1. 메인 웹페이지(index.html) 서빙
@app.route('/')
def home():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    index_path = os.path.join(base_dir, 'index.html')
    return send_file(index_path)

# 2. 인기 검색어 데이터 API (searchlist.xlsx)
@app.route('/api/trending')
def get_trending():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    file_path = os.path.join(base_dir, 'static', 'searchlist.xlsx')
    try:
        if not os.path.exists(file_path):
            return jsonify([])
            
        wb = openpyxl.load_workbook(file_path, data_only=True)
        sheet = wb.active
        search_terms = [str(row[0]).strip() for row in sheet.iter_rows(min_col=1, max_col=1, values_only=True) if row[0]]
        counter = Counter(search_terms)
        top_3 = counter.most_common(3)
        results = [{'id': idx + 1, 'term': item[0]} for idx, item in enumerate(top_3)]
        return jsonify(results)
    except Exception as e:
        print(f"인기 검색어 엑셀 읽기 오류: {e}")
        return jsonify([])

# 3. 화면 표시용 최근 리뷰 API (대상자별 최신 3개 제한)
@app.route('/api/reviews/recent')
def get_recent_reviews():
    target = request.args.get('target', '')
    base_dir = os.path.dirname(os.path.abspath(__file__))
    file_path = os.path.join(base_dir, 'static', 'review.xlsx')
    try:
        if not os.path.exists(file_path):
            return jsonify([])
        
        wb = openpyxl.load_workbook(file_path, data_only=True)
        sheet = wb.active
        
        reviews = []
        for row in sheet.iter_rows(min_row=2, values_only=True):
            if any(row): 
                row_target = str(row[4]).strip() if len(row) > 4 and row[4] else ''
                if row_target == str(target).strip():
                    reviews.append({
                        'userId': str(row[0]) if row[0] else '익명',
                        'date': str(row[1]) if row[1] else '',
                        'content': str(row[2]) if row[2] else '',
                        'rating': int(row[3]) if row[3] else 5
                    })
                    if len(reviews) >= 3:
                        break
        return jsonify(reviews)
    except Exception as e:
        print(f"최근 리뷰 불러오기 오류: {e}")
        return jsonify([])

# 4. 리뷰 저장 API (항상 2행에 삽입하여 최신순 유지)
@app.route('/api/review', methods=['POST'])
def save_review():
    try:
        data = request.json
        user_id = data.get('userId', '익명')
        content = data.get('content', '')
        rating = data.get('rating', '5')
        target_id = data.get('targetId', '') 
        
        date_str = datetime.now().strftime('%Y-%m-%d %H:%M')
        
        base_dir = os.path.dirname(os.path.abspath(__file__))
        file_path = os.path.join(base_dir, 'static', 'review.xlsx')
        
        if os.path.exists(file_path):
            wb = openpyxl.load_workbook(file_path)
            sheet = wb.active
        else:
            wb = openpyxl.Workbook()
            sheet = wb.active
            sheet.append(['아이디', '작성일', '내용', '별점', '대상자(Ax)'])
            
        sheet.insert_rows(2)
        sheet.cell(row=2, column=1, value=user_id)
        sheet.cell(row=2, column=2, value=date_str)
        sheet.cell(row=2, column=3, value=content)
        sheet.cell(row=2, column=4, value=rating)
        sheet.cell(row=2, column=5, value=target_id)
        
        wb.save(file_path)
        
        return jsonify({'success': True, 'message': '리뷰가 저장되었습니다.'})
        
    except Exception as e:
        print(f"리뷰 엑셀 저장 중 오류 발생: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

# 5. Gemini AI 분석 API (보안을 위한 환경 변수 사용 및 전체 리뷰 분석 기능)
@app.route('/api/ai/analyze', methods=['POST'])
def analyze_judge():
    try:
        data = request.json
        target_id = data.get('targetId', '')
        if not target_id:
            return jsonify({'success': False, 'message': '분석 대상자가 없습니다.'})

        base_dir = os.path.dirname(os.path.abspath(__file__))
        file_path = os.path.join(base_dir, 'static', 'review.xlsx')
        review_context = ""
        
        # 엑셀에서 해당 대상자의 '전체' 리뷰를 수집하여 프롬프트 재료로 구성
        if os.path.exists(file_path):
            wb = openpyxl.load_workbook(file_path, data_only=True)
            sheet = wb.active
            reviews = []
            for row in sheet.iter_rows(min_row=2, values_only=True):
                if any(row): 
                    row_target = str(row[4]).strip() if len(row) > 4 and row[4] else ''
                    if row_target == str(target_id).strip():
                        reviews.append({'rating': int(row[3]) if row[3] else 5, 'content': str(row[2]) if row[2] else ''})
            
            if reviews:
                review_context = "다음은 이 법관에 대해 실제 시민들이 남긴 사이트 내 전체 리뷰 데이터입니다:\n"
                for idx, r in enumerate(reviews):
                    review_context += f"{idx + 1}. 별점 {r['rating']}점: \"{r['content']}\"\n"
                review_context += "\n\n"
            else:
                review_context = "현재 이 법관에 대해 플랫폼에 등록된 시민 리뷰는 없습니다.\n\n"
        
        prompt_text = f"당신은 '사법의 창'이라는 플랫폼의 수석 AI 법률 데이터 분석관입니다. 사용자가 '{target_id}'(판사/검사)에 대한 종합 분석을 요청했습니다.\n\n{review_context}위의 데이터(별점 및 내용)를 반드시 분석에 적극적으로 반영하여, 이 법관의 재판 진행 스타일, 특징, 시민들의 평가를 종합한 분석 리포트를 3문장으로 전문성 있게 요약해주세요. (마지막에는 실제 인물이 아닌 테스트 데모임을 명시해주세요.)"

        # Render 서버 환경 변수에서 구글 API 키를 안전하게 불러옵니다.
        GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY', '') 
        endpoint = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash-preview-09-2025:generateContent?key={GEMINI_API_KEY}"
        
        payload = {"contents": [{"parts": [{"text": prompt_text}]}]}
        
        # 보안 이슈 없이 백엔드에서 Google API와 직접 통신
        response = requests.post(endpoint, json=payload, headers={'Content-Type': 'application/json'})
        
        if response.status_code == 200:
            res_data = response.json()
            text = res_data.get('candidates', [{}])[0].get('content', {}).get('parts', [{}])[0].get('text', '')
            if text:
                return jsonify({'success': True, 'text': text})
        
        return jsonify({'success': False, 'message': 'API 키 설정이나 통신 문제로 AI 분석 결과를 받아오지 못했습니다.'})
        
    except Exception as e:
        print(f"AI 분석 오류: {e}")
        return jsonify({'success': False, 'message': '서버 처리 중 오류가 발생했습니다.'})

if __name__ == '__main__':
    # Render 플랫폼 배포 포트에 맞추어 실행
    app.run(host='0.0.0.0', port=10000)
