import os
from flask import Flask, send_file, jsonify, request
import openpyxl
from collections import Counter
from datetime import datetime

app = Flask(__name__, static_folder='static')

@app.route('/')
def home():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    index_path = os.path.join(base_dir, 'index.html')
    return send_file(index_path)

@app.route('/api/trending')
def get_trending():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    file_path = os.path.join(base_dir, 'static', 'searchlist.xlsx')
    try:
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

# [화면 UI 용] 최근 리뷰 3개만 불러오기
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
                    if len(reviews) >= 3: # 딱 3개까지만 제한
                        break
        return jsonify(reviews)
    except Exception as e:
        print(f"최근 리뷰 불러오기 오류: {e}")
        return jsonify([])

# [Gemini AI 용] 해당 법관의 '전체 리뷰' 모조리 불러오기
@app.route('/api/reviews/all')
def get_all_reviews():
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
                        'rating': int(row[3]) if row[3] else 5,
                        'content': str(row[2]) if row[2] else ''
                    })
                    # 3개 제한 없이 일치하는 것은 무한정 모두 배열에 담습니다.
        return jsonify(reviews)
    except Exception as e:
        print(f"전체 리뷰 불러오기 오류: {e}")
        return jsonify([])

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

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)
