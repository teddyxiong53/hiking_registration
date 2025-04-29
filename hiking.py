from flask import Flask, render_template, request, jsonify, g
import sqlite3
import os
import json
from datetime import datetime

app = Flask(__name__)

# 数据库配置
DATABASE = 'hiking_registration.db'

def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
        db.row_factory = sqlite3.Row
    return db

@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()

def init_db():
    with app.app_context():
        db = get_db()
        with app.open_resource('schema.sql', mode='r') as f:
            db.cursor().executescript(f.read())
        db.commit()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/teams', methods=['GET'])
def get_teams():
    db = get_db()
    cursor = db.cursor()

    # 获取所有团队信息
    cursor.execute('''
        SELECT team_id, team_name, max_members
        FROM teams
        ORDER BY team_name
    ''')
    teams = []
    for row in cursor.fetchall():
        team = dict(row)

        # 获取每个团队的成员数
        cursor.execute('''
            SELECT COUNT(*) as member_count
            FROM members
            WHERE team_id = ?
        ''', (row['team_id'],))
        member_count = cursor.fetchone()['member_count']
        team['member_count'] = member_count

        # 获取队长信息
        cursor.execute('''
            SELECT name
            FROM members
            WHERE team_id = ? AND is_captain = 1
        ''', (row['team_id'],))
        captain = cursor.fetchone()
        team['captain'] = captain['name'] if captain else None

        # 获取成员列表
        cursor.execute('''
            SELECT id, name, gender, phone, is_captain
            FROM members
            WHERE team_id = ?
        ''', (row['team_id'],))
        members = [dict(member) for member in cursor.fetchall()]
        team['members'] = members

        teams.append(team)

    return jsonify(teams)

@app.route('/api/register', methods=['POST'])
def register():
    data = request.json
    name = data.get('name')
    gender = data.get('gender')
    phone = data.get('phone')
    team_id = data.get('team_id')
    is_captain = 1 if data.get('isCaptain') else 0

    db = get_db()
    cursor = db.cursor()

    # 检查该组是否已满
    cursor.execute('''
        SELECT COUNT(*) as member_count, t.max_members
        FROM members m
        JOIN teams t ON m.team_id = t.team_id
        WHERE m.team_id = ?
        GROUP BY m.team_id
    ''', (team_id,))

    result = cursor.fetchone()
    if result and result['member_count'] >= result['max_members']:
        return jsonify({'success': False, 'message': '该组已满，请选择其他组'}), 400

    # 检查该组是否已有队长
    if is_captain:
        cursor.execute('''
            SELECT COUNT(*) as captain_count
            FROM members
            WHERE team_id = ? AND is_captain = 1
        ''', (team_id,))

        if cursor.fetchone()['captain_count'] > 0:
            return jsonify({'success': False, 'message': '该组已有队长，不能再选择成为队长'}), 400

    # 插入新成员
    cursor.execute('''
        INSERT INTO members (name, gender, phone, team_id, is_captain, register_time)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (name, gender, phone, team_id, is_captain, datetime.now().strftime('%Y-%m-%d %H:%M:%S')))

    db.commit()

    return jsonify({'success': True, 'message': '报名成功！'})

# 管理界面路由
@app.route('/admin')
def admin():
    return render_template('admin.html')

# 管理接口 - 删除成员
@app.route('/api/delete_member/<int:member_id>', methods=['DELETE'])
def delete_member(member_id):
    db = get_db()
    cursor = db.cursor()

    cursor.execute('DELETE FROM members WHERE id = ?', (member_id,))
    db.commit()

    return jsonify({'success': True, 'message': '成员已删除'})

if __name__ == '__main__':
    if not os.path.exists(DATABASE):
        # 确保schema.sql存在
        with open('schema.sql', 'w') as f:
            f.write('''
            DROP TABLE IF EXISTS teams;
            DROP TABLE IF EXISTS members;

            CREATE TABLE teams (
                team_id INTEGER PRIMARY KEY AUTOINCREMENT,
                team_name TEXT NOT NULL,
                max_members INTEGER NOT NULL DEFAULT 8
            );

            CREATE TABLE members (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                gender TEXT NOT NULL,
                phone TEXT NOT NULL,
                team_id INTEGER NOT NULL,
                is_captain INTEGER NOT NULL DEFAULT 0,
                register_time TEXT NOT NULL,
                FOREIGN KEY (team_id) REFERENCES teams (team_id)
            );

            -- 初始化14个组
            INSERT INTO teams (team_name, max_members) VALUES
                ('A', 8), ('B', 8), ('C', 8), ('D', 8), ('E', 8), ('F', 8), ('G', 8),
                ('H', 8), ('I', 8), ('J', 8), ('K', 8), ('L', 8), ('M', 8), ('N', 8);
            ''')
        init_db()

    app.run(host='0.0.0.0', port=5000, debug=True)