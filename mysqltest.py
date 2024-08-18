from flask import Flask,send_file
from flask_sqlalchemy import SQLAlchemy
from flask import jsonify,json,request
from flask_cors import CORS
import os
import uuid
from werkzeug.utils import secure_filename
import win32print
import win32api


# アップロード先のディレクトリを設定
UPLOAD_FOLDER = 'uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'
CORS(app)


#sqlalchemyで用いるDBの設定
app.config['SQLALCHEMY_DATABASE_URI'] = \
    "mysql+pymysql://{user}:{password}@{host}/{dbName}?charset=utf8".format(
        user='root',
        password='hirokintv1mysql',
        host='localhost:3306',
        dbName='freestep'
    )

db = SQLAlchemy(app)

#モデルクラスの作成(テーブル定義)
class Grade(db.Model):
    __tablename__ = 'grades'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(50), nullable=False)

    subjects = db.relationship('Subject', backref='grade', lazy=True)


class Subject(db.Model):
    __tablename__ = 'subjects'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(50), nullable=False)
    grade_id = db.Column(db.Integer, db.ForeignKey('grades.id'))

    units = db.relationship('Unit', backref='subject', lazy=True)


class Unit(db.Model):
    __tablename__ = 'units'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(100), nullable=False)
    subject_id = db.Column(db.Integer, db.ForeignKey('subjects.id'))



class Problem(db.Model):
    __tablename__ = 'problems'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    
    # Remove grade, subject, unit columns and replace with foreign key columns
    grade_id = db.Column(db.Integer, db.ForeignKey('grades.id'), nullable=False)
    subject_id = db.Column(db.Integer, db.ForeignKey('subjects.id'), nullable=False)
    unit_id = db.Column(db.Integer, db.ForeignKey('units.id'), nullable=False)
    
    difficulty = db.Column(db.Enum('0', '1', '2', '3', '4', '5'), nullable=False)
    file_path = db.Column(db.String(255), nullable=False)
    upload_date = db.Column(db.DateTime, nullable=False, default=db.func.current_timestamp())
    title = db.Column(db.String(255), nullable=False)
    memo = db.Column(db.Text)

    # Define relationships (optional, if you want to access related data easily)
    grade = db.relationship('Grade', backref=db.backref('problems', lazy=True))
    subject = db.relationship('Subject', backref=db.backref('problems', lazy=True))
    unit = db.relationship('Unit', backref=db.backref('problems', lazy=True))

# class Problem(db.Model):
#     __tablename__ = 'problems'
#     id = db.Column(db.Integer, primary_key=True, autoincrement=True)
#     grade = db.Column(db.String(10), nullable=False)
#     subject = db.Column(db.String(50), nullable=False)
#     unit = db.Column(db.String(100), nullable=False)
#     difficulty = db.Column(db.Enum('0', '1', '2', '3', '4', '5'), nullable=False)
#     file_path = db.Column(db.String(255), nullable=False)
#     upload_date = db.Column(db.DateTime, nullable=False, default=db.func.current_timestamp())
#     title = db.Column(db.String(255), nullable=False)
#     memo = db.Column(db.Text)



#grade全件取得api
@app.route('/get/grades/all',methods=['GET'])
def get_grades_all():
    grades = Grade.query.all()
    # Gradeオブジェクトを辞書形式に変換してリスト化
    grades_list = [{'id': grade.id, 'name': grade.name} for grade in grades]

    # JSON形式で返す
    # JSON形式で返す際にensure_ascii=Falseを指定
    response = jsonify(grades_list)
    response.data = json.dumps(grades_list, ensure_ascii=False).encode('utf-8')
    return response

#subject全件取得api
@app.route('/get/subjects/all',methods=['GET'])
def get_subjects_all():
    subjects = Subject.query.all()
    subjects_list = [{'id':subject.id, 'name': subject.name, 'grade_id': subject.grade_id} for subject in subjects]

    response = jsonify(subjects_list)
    response.data = json.dumps(subjects_list, ensure_ascii=False).encode('utf-8')
    return response

#unit全件取得api
@app.route('/get/units/all',methods=['GET'])
def get_units_all():
    units = Unit.query.all()
    units_list = [{'id': unit.id, 'name': unit.name, 'subject_id': unit.subject_id} for unit in units]
    response = jsonify(units_list)
    response.data = json.dumps(units_list, ensure_ascii=False).encode('utf-8')
    return response

#subjectidに対応するunit取得api
@app.route('/get/units/<int:subject_id>',methods=['GET'])
def get_units_byId(subject_id):
    units = Unit.query.filter_by(subject_id = subject_id)
    units_list = [{'id': unit.id, 'name': unit.name, 'subject_id': unit.subject_id} for unit in units]
    response = jsonify(units_list)
    response.data = json.dumps(units_list, ensure_ascii=False).encode('utf-8')
    return response


#unit追加api
@app.route('/insert/unit',methods=['POST'])
def insert_unit():
    data = request.json
    name = data.get('name')
    subject_id = data.get('subject_id')

    new_unit = Unit(name=name, subject_id=subject_id)
    db.session.add(new_unit)
    db.session.commit()
    return jsonify({'message': 'Unit added successfully'})

#unitの編集
@app.route('/update/unit/<int:unit_id>',methods=['PUT'])
def update_unit(unit_id):
    data = request.json
    unit = Unit.query.get_or_404(unit_id)
    unit.name = data.get('name', unit.name)
    db.session.commit()
    return jsonify({'message': 'Unit updated successfully'})

#unitの削除
@app.route('/delete/unit/<int:unit_id>', methods=['DELETE'])
def delete_unit(unit_id):
    unit = Unit.query.get_or_404(unit_id)
    
    # problemで使われているかどうかのチェック
    problems_using_unit = Problem.query.filter_by(unit_id=unit_id).first()
    
    if problems_using_unit:
        return jsonify({'message': 'Cannot delete unit. It is being used in one or more problems.'}), 400
    
    # 使われていなければ削除する
    db.session.delete(unit)
    db.session.commit()
    return jsonify({'message': 'Unit deleted successfully'})


#problem取得api
@app.route('/get/problems', methods=['GET'])
def get_problems():
    grade = request.args.get('grade')
    subject = request.args.get('subject')

    query = Problem.query

    if grade:
        query = query.filter_by(grade_id = grade)
    if subject:
        query = query.filter_by(subject_id = subject)
    
    problems = query.all()
    problems_list = [{
        'id': problem.id,
        'grade': Grade.query.get_or_404(problem.grade_id).name,
        'grade_id': problem.grade_id,
        'subject': Subject.query.get_or_404(problem.subject_id).name,
        'subject_id': problem.subject_id,
        'unit': Unit.query.get_or_404(problem.unit_id).name,
        'unit_id': problem.unit_id,
        'difficulty': problem.difficulty,
        'file_path': problem.file_path,
        'upload_date': problem.upload_date.strftime('%Y-%m-%d %H:%M:%S'),  # 日時を文字列に変換
        'title': problem.title,
        'memo': problem.memo
    } for problem in problems]
    
    response = jsonify(problems_list)
    response.data = json.dumps(problems_list, ensure_ascii=False).encode('utf-8')
    return response

#problem追加api
@app.route('/insert/problem', methods=['POST'])
def insert_problem():
    file = request.files.get('file')
    title = request.form.get('title')
    grade = request.form.get('grade')
    subject = request.form.get('subject')
    unit = request.form.get('unit')
    difficulty = request.form.get('difficulty')
    memo = request.form.get('memo', '')  # Memo is optional

    if file:
        filename = secure_filename(file.filename)  # Ensure safe filename
        unique_filename = str(uuid.uuid4()) + "_" + filename
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
        file.save(file_path)

        # 'upload_date' is automatically set to the current timestamp by SQLAlchemy
        problem = Problem(
            grade_id=grade,
            subject_id=subject,
            unit_id=unit,
            difficulty=difficulty,
            file_path=file_path,
            title=title,
            memo=memo
        )
        db.session.add(problem)
        db.session.commit()

        return jsonify({'message': 'Problem added successfully'}), 201

    return jsonify({'error': 'File is required'}), 400


#problem編集api
@app.route('/edit/problem/<int:id>', methods=['PUT'])
def update_problem(id):
    problem = Problem.query.get_or_404(id)
    
    problem.grade_id = request.form.get('grade')
    problem.subject_id = request.form.get('subject')
    problem.unit_id = request.form.get('unit')
    problem.title = request.form.get('title')
    problem.difficulty = request.form.get('difficulty')
    
    db.session.commit()
    return jsonify({'message': 'Problem updated successfully'})

#problem削除api
@app.route('/delete/problem/<int:id>',methods=['DELETE'])
def delete_problem(id):
    problem = Problem.query.get_or_404(id)
    os.remove(problem.file_path)
    db.session.delete(problem)
    db.session.commit()
    return jsonify({'message': 'problem deleted successfully'})





#problem_idに対応したpdf送信api
@app.route('/get-pdf/<int:problem_id>')
def get_pdf(problem_id):
    problem = Problem.query.get_or_404(problem_id)
    return send_file(problem.file_path,as_attachment=False)
    



# @app.route('/get-pdf',methods=['GET'])
# def get_pdf():
#     file_path = r'C:\Users\hirokikawai\Downloads\final_exam.pdf'
#     return send_file(file_path,as_attachment=False)


# @app.route('/upload', methods=['POST'])
# def upload_file():
#     if 'file' not in request.files:
#         return jsonify({'error': 'No file part'}), 400

#     file = request.files['file']

#     if file.filename == '':
#         return jsonify({'error': 'No selected file'}), 400

#     if file:
#         # 一意のファイル名を生成
#         unique_filename = f"{uuid.uuid4()}_{file.filename}"
#         filepath = os.path.join(UPLOAD_FOLDER, unique_filename)
#         file.save(filepath)
#         return jsonify({'message': 'File uploaded successfully', 'filepath': filepath}), 200
    


#problem印刷api
@app.route('/print/<int:problem_id>')
def print_problem(problem_id):
    try:
        problem = Problem.query.get_or_404(problem_id)
        
        # デフォルトプリンタを取得
        printer_name = win32print.GetDefaultPrinter()
        
        if not printer_name:
            return jsonify({'message': 'Default printer not found'}), 500
        
        # 印刷コマンドを実行
        win32api.ShellExecute(
            0,
            "print",
            problem.file_path,
            None,
            ".",
            0
        )
        
        return jsonify({'message': 'File printed successfully'})

    except FileNotFoundError:
        return jsonify({'message': 'File not found'}), 404
    
    except win32api.error as e:
        return jsonify({'message': f'Print operation failed: {str(e)}'}), 500
    
    except Exception as e:
        return jsonify({'message': f'An unexpected error occurred: {str(e)}'}), 500











if __name__ == '__main__':
    app.run(debug=True, host='192.168.3.114', port=5000)