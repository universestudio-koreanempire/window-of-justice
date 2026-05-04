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

@app.route('/api/review', methods=['POST'])
def save_review():
    try:
        data = request.json
        user_id = data.get('userId', '익명')
        content = data.get('content', '')
        rating = data.get('rating', '5')
        
        date_str = datetime.now().strftime('%Y-%m-%d %H:%M')
        
        base_dir = os.path.dirname(os.path.abspath(__file__))
        file_path = os.path.join(base_dir, 'static', 'review.xlsx')
        
        if os.path.exists(file_path):
            wb = openpyxl.load_workbook(file_path)
            sheet = wb.active
        else:
            wb = openpyxl.Workbook()
            sheet = wb.active
            sheet.append(['아이디', '작성일', '내용', '별점'])
            
        sheet.insert_rows(2)
        sheet.cell(row=2, column=1, value=user_id)
        sheet.cell(row=2, column=2, value=date_str)
        sheet.cell(row=2, column=3, value=content)
        sheet.cell(row=2, column=4, value=rating)
        
        wb.save(file_path)
        
        return jsonify({'success': True, 'message': '리뷰가 저장되었습니다.'})
        
    except Exception as e:
        print(f"리뷰 엑셀 저장 중 오류 발생: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)
