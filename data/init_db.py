"""初始化公司数据库

创建员工、部门、薪资相关表，并插入测试数据。
"""

import sqlite3
import os
from datetime import date, datetime, timedelta
import random

DATABASE_PATH = os.path.join(os.path.dirname(__file__), 'company.db')


def create_tables(conn):
    """创建数据库表结构"""
    cursor = conn.cursor()
    
    # 部门表
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS departments (
        dept_id INTEGER PRIMARY KEY AUTOINCREMENT,
        dept_name VARCHAR(50) NOT NULL UNIQUE,
        location VARCHAR(100),
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')
    
    # 员工表
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS employees (
        emp_id INTEGER PRIMARY KEY AUTOINCREMENT,
        emp_name VARCHAR(50) NOT NULL,
        dept_id INTEGER,
        position VARCHAR(50),
        hire_date DATE NOT NULL,
        email VARCHAR(100) UNIQUE,
        phone VARCHAR(20),
        FOREIGN KEY (dept_id) REFERENCES departments(dept_id)
    )
    ''')
    
    # 薪资表
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS salaries (
        salary_id INTEGER PRIMARY KEY AUTOINCREMENT,
        emp_id INTEGER NOT NULL,
        base_salary DECIMAL(10, 2) NOT NULL,
        bonus DECIMAL(10, 2) DEFAULT 0,
        effective_date DATE NOT NULL,
        FOREIGN KEY (emp_id) REFERENCES employees(emp_id)
    )
    ''')
    
    # 创建索引提升查询性能
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_emp_dept ON employees(dept_id)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_salary_emp ON salaries(emp_id)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_salary_date ON salaries(effective_date)')
    
    conn.commit()


def insert_sample_data(conn):
    """插入示例数据"""
    cursor = conn.cursor()
    
    # 清空现有数据
    cursor.execute('DELETE FROM salaries')
    cursor.execute('DELETE FROM employees')
    cursor.execute('DELETE FROM departments')
    
    # 重置自增ID计数器
    cursor.execute('DELETE FROM sqlite_sequence WHERE name IN ("departments", "employees", "salaries")')
    
    # 插入部门数据
    departments = [
        ('研发部', '北京'),
        ('市场部', '上海'),
        ('人事部', '北京'),
        ('财务部', '北京'),
        ('销售部', '广州'),
        ('运营部', '深圳'),
        ('技术支持部', '北京'),
        ('产品部', '上海'),
        ('设计部', '深圳'),
        ('客服部', '广州'),
        ('采购部', '北京'),
        ('法务部', '上海')
    ]
    
    cursor.executemany(
        'INSERT INTO departments (dept_name, location) VALUES (?, ?)',
        departments
    )
    
    # 获取部门ID映射
    cursor.execute('SELECT dept_id, dept_name FROM departments')
    dept_map = {name: dept_id for dept_id, name in cursor.fetchall()}
    
    # 员工数据
    employees = [
        # 研发部 (12人)
        ('张三', dept_map['研发部'], '高级工程师', '2020-03-15', 'zhangsan@company.com', '13800138001'),
        ('李四', dept_map['研发部'], '工程师', '2021-06-20', 'lisi@company.com', '13800138002'),
        ('王五', dept_map['研发部'], '技术经理', '2019-01-10', 'wangwu@company.com', '13800138003'),
        ('赵六', dept_map['研发部'], '架构师', '2018-08-05', 'zhaoliu@company.com', '13800138004'),
        ('孙七', dept_map['研发部'], '工程师', '2022-02-28', 'sunqi@company.com', '13800138005'),
        ('钱大', dept_map['研发部'], '高级工程师', '2020-07-12', 'qianda@company.com', '13800138018'),
        ('陈二', dept_map['研发部'], '工程师', '2022-05-18', 'chener@company.com', '13800138019'),
        ('刘明', dept_map['研发部'], '工程师', '2023-01-08', 'liuming@company.com', '13800138020'),
        ('张伟', dept_map['研发部'], '高级工程师', '2019-09-20', 'zhangwei@company.com', '13800138021'),
        ('王芳', dept_map['研发部'], '测试工程师', '2021-11-05', 'wangfang@company.com', '13800138022'),
        ('李娜', dept_map['研发部'], '测试工程师', '2022-08-15', 'lina@company.com', '13800138023'),
        ('赵强', dept_map['研发部'], '工程师', '2023-03-22', 'zhaoqiang@company.com', '13800138024'),
        
        # 市场部 (8人)
        ('周八', dept_map['市场部'], '市场经理', '2020-05-10', 'zhouba@company.com', '13800138006'),
        ('吴九', dept_map['市场部'], '市场专员', '2021-09-15', 'wujiu@company.com', '13800138007'),
        ('郑十', dept_map['市场部'], '品牌经理', '2019-12-01', 'zhengshi@company.com', '13800138008'),
        ('孙丽', dept_map['市场部'], '市场专员', '2022-04-10', 'sunli@company.com', '13800138025'),
        ('周杰', dept_map['市场部'], '市场专员', '2022-07-20', 'zhoujie@company.com', '13800138026'),
        ('吴静', dept_map['市场部'], '活动策划', '2021-05-15', 'wujing@company.com', '13800138027'),
        ('郑云', dept_map['市场部'], '活动策划', '2023-02-08', 'zhengyun@company.com', '13800138028'),
        ('冯霞', dept_map['市场部'], '市场专员', '2023-06-12', 'fengxia@company.com', '13800138029'),
        
        # 人事部 (6人)
        ('陈晓', dept_map['人事部'], '人事经理', '2019-07-20', 'chenxiao@company.com', '13800138009'),
        ('林涛', dept_map['人事部'], '招聘专员', '2021-03-10', 'lintao@company.com', '13800138010'),
        ('许敏', dept_map['人事部'], '招聘专员', '2022-01-18', 'xumin@company.com', '13800138030'),
        ('何洁', dept_map['人事部'], '培训专员', '2021-08-25', 'hejie@company.com', '13800138031'),
        ('韩梅', dept_map['人事部'], '薪酬专员', '2020-11-30', 'hanmei@company.com', '13800138032'),
        ('曹雪', dept_map['人事部'], '行政专员', '2022-09-05', 'caoxue@company.com', '13800138033'),
        
        # 财务部 (7人)
        ('黄梅', dept_map['财务部'], '财务经理', '2018-11-15', 'huangmei@company.com', '13800138011'),
        ('杨柳', dept_map['财务部'], '会计', '2020-08-25', 'yangliu@company.com', '13800138012'),
        ('朱红', dept_map['财务部'], '会计', '2021-06-10', 'zhuhong@company.com', '13800138034'),
        ('秦岚', dept_map['财务部'], '出纳', '2022-03-15', 'qinlan@company.com', '13800138035'),
        ('尤敏', dept_map['财务部'], '税务专员', '2020-12-20', 'youmin@company.com', '13800138036'),
        ('许晴', dept_map['财务部'], '会计', '2023-01-25', 'xuqing@company.com', '13800138037'),
        ('沈丹', dept_map['财务部'], '财务助理', '2023-04-10', 'shendan@company.com', '13800138038'),
        
        # 销售部 (10人)
        ('徐峰', dept_map['销售部'], '销售总监', '2017-06-30', 'xufeng@company.com', '13800138013'),
        ('马强', dept_map['销售部'], '销售经理', '2019-04-15', 'maqiang@company.com', '13800138014'),
        ('刘洋', dept_map['销售部'], '销售专员', '2021-11-20', 'liuyang@company.com', '13800138015'),
        ('范冰', dept_map['销售部'], '销售专员', '2022-02-14', 'fanbing@company.com', '13800138039'),
        ('彭飞', dept_map['销售部'], '销售专员', '2022-05-20', 'pengfei@company.com', '13800138040'),
        ('饶雪', dept_map['销售部'], '销售专员', '2021-09-08', 'raoxue@company.com', '13800138041'),
        ('陆军', dept_map['销售部'], '销售经理', '2020-03-12', 'lujun@company.com', '13800138042'),
        ('梁静', dept_map['销售部'], '销售专员', '2023-01-05', 'liangjing@company.com', '13800138043'),
        ('温柔', dept_map['销售部'], '销售专员', '2023-03-18', 'wenrou@company.com', '13800138044'),
        ('游勇', dept_map['销售部'], '大客户经理', '2019-08-22', 'youyong@company.com', '13800138045'),
        
        # 运营部 (7人)
        ('胡军', dept_map['运营部'], '运营经理', '2020-01-05', 'hujun@company.com', '13800138016'),
        ('邓丽', dept_map['运营部'], '运营专员', '2021-07-15', 'dengli@company.com', '13800138017'),
        ('袁媛', dept_map['运营部'], '运营专员', '2022-04-20', 'yuanyuan@company.com', '13800138046'),
        ('卫平', dept_map['运营部'], '数据分析师', '2021-10-15', 'weiping@company.com', '13800138047'),
        ('蒋丽', dept_map['运营部'], '运营专员', '2022-12-08', 'jiangli@company.com', '13800138048'),
        ('韩冰', dept_map['运营部'], '内容运营', '2023-02-20', 'hanbing@company.com', '13800138049'),
        ('鲁迅', dept_map['运营部'], '运营专员', '2023-05-15', 'luxun@company.com', '13800138050'),
        
        # 技术支持部 (6人)
        ('苗青', dept_map['技术支持部'], '技术支持经理', '2019-05-10', 'miaoqing@company.com', '13800138051'),
        ('凌霜', dept_map['技术支持部'], '技术支持', '2021-08-12', 'lingshuang@company.com', '13800138052'),
        ('柏雪', dept_map['技术支持部'], '技术支持', '2022-03-20', 'baixue@company.com', '13800138053'),
        ('水清', dept_map['技术支持部'], '技术支持', '2022-09-15', 'shuiqing@company.com', '13800138054'),
        ('花香', dept_map['技术支持部'], '技术支持', '2023-01-10', 'huaxiang@company.com', '13800138055'),
        ('叶绿', dept_map['技术支持部'], '技术文档', '2021-11-22', 'yelv@company.com', '13800138056'),
        
        # 产品部 (7人)
        ('司马光', dept_map['产品部'], '产品总监', '2018-03-15', 'simaguang@company.com', '13800138057'),
        ('欧阳修', dept_map['产品部'], '产品经理', '2020-06-20', 'ouyangxiu@company.com', '13800138058'),
        ('诸葛亮', dept_map['产品部'], '产品经理', '2021-04-10', 'zhugeliang@company.com', '13800138059'),
        ('上官婉儿', dept_map['产品部'], '产品助理', '2022-07-15', 'shangguanwaner@company.com', '13800138060'),
        ('东方朔', dept_map['产品部'], '产品专员', '2022-10-20', 'dongfangshuo@company.com', '13800138061'),
        ('西门庆', dept_map['产品部'], '产品专员', '2023-02-28', 'ximenqing@company.com', '13800138062'),
        ('南宫紫', dept_map['产品部'], '产品专员', '2023-05-12', 'nangongzi@company.com', '13800138063'),
        
        # 设计部 (6人)
        ('夏侯惇', dept_map['设计部'], '设计总监', '2019-02-10', 'xiahoudun@company.com', '13800138064'),
        ('关羽', dept_map['设计部'], 'UI设计师', '2020-09-15', 'guanyu@company.com', '13800138065'),
        ('张飞', dept_map['设计部'], 'UI设计师', '2021-05-20', 'zhangfei@company.com', '13800138066'),
        ('赵云', dept_map['设计部'], 'UX设计师', '2021-12-10', 'zhaoyun@company.com', '13800138067'),
        ('马超', dept_map['设计部'], '平面设计师', '2022-08-15', 'machao@company.com', '13800138068'),
        ('黄忠', dept_map['设计部'], '平面设计师', '2023-03-20', 'huangzhong@company.com', '13800138069'),
        
        # 客服部 (5人)
        ('貂蝉', dept_map['客服部'], '客服经理', '2020-04-10', 'diaochan@company.com', '13800138070'),
        ('王昭君', dept_map['客服部'], '客服专员', '2021-07-15', 'wangzhaojun@company.com', '13800138071'),
        ('杨玉环', dept_map['客服部'], '客服专员', '2022-01-20', 'yangyuhuan@company.com', '13800138072'),
        ('西施', dept_map['客服部'], '客服专员', '2022-09-10', 'xishi@company.com', '13800138073'),
        ('花木兰', dept_map['客服部'], '客服组长', '2021-03-25', 'huamulan@company.com', '13800138074'),
        
        # 采购部 (4人)
        ('刘备', dept_map['采购部'], '采购经理', '2019-06-15', 'liubei@company.com', '13800138075'),
        ('孙权', dept_map['采购部'], '采购专员', '2021-08-20', 'sunquan@company.com', '13800138076'),
        ('曹操', dept_map['采购部'], '采购专员', '2022-04-15', 'caocao@company.com', '13800138077'),
        ('董卓', dept_map['采购部'], '采购助理', '2023-01-10', 'dongzhuo@company.com', '13800138078'),
        
        # 法务部 (4人)
        ('包拯', dept_map['法务部'], '法务总监', '2018-09-20', 'baozheng@company.com', '13800138079'),
        ('狄仁杰', dept_map['法务部'], '法务经理', '2020-11-15', 'direnjie@company.com', '13800138080'),
        ('宋慈', dept_map['法务部'], '法务专员', '2022-03-10', 'songci@company.com', '13800138081'),
        ('海瑞', dept_map['法务部'], '法务专员', '2022-12-05', 'hairui@company.com', '13800138082'),
    ]
    
    cursor.executemany('''
        INSERT INTO employees (emp_name, dept_id, position, hire_date, email, phone)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', employees)
    
    # 获取员工ID
    cursor.execute('SELECT emp_id, emp_name FROM employees')
    emp_map = {name: emp_id for emp_id, name in cursor.fetchall()}
    
    # 薪资数据（基于职位和入职时间）
    salary_rules = {
        '工程师': (8000, 15000),
        '高级工程师': (15000, 25000),
        '技术经理': (25000, 35000),
        '架构师': (30000, 45000),
        '测试工程师': (8000, 15000),
        '市场专员': (6000, 10000),
        '市场经理': (15000, 25000),
        '品牌经理': (18000, 28000),
        '活动策划': (7000, 12000),
        '人事经理': (12000, 20000),
        '招聘专员': (6000, 10000),
        '培训专员': (6000, 10000),
        '薪酬专员': (7000, 12000),
        '行政专员': (5000, 9000),
        '财务经理': (15000, 25000),
        '会计': (8000, 12000),
        '出纳': (6000, 9000),
        '税务专员': (8000, 13000),
        '财务助理': (5000, 8000),
        '销售总监': (30000, 50000),
        '销售经理': (20000, 35000),
        '销售专员': (5000, 15000),
        '大客户经理': (25000, 40000),
        '运营经理': (15000, 25000),
        '运营专员': (6000, 10000),
        '数据分析师': (12000, 22000),
        '内容运营': (7000, 12000),
        '技术支持经理': (15000, 25000),
        '技术支持': (7000, 12000),
        '技术文档': (8000, 13000),
        '产品总监': (30000, 50000),
        '产品经理': (20000, 35000),
        '产品专员': (8000, 15000),
        '产品助理': (6000, 10000),
        '设计总监': (25000, 40000),
        'UI设计师': (10000, 20000),
        'UX设计师': (12000, 22000),
        '平面设计师': (8000, 15000),
        '客服经理': (10000, 18000),
        '客服专员': (5000, 8000),
        '客服组长': (8000, 13000),
        '采购经理': (15000, 25000),
        '采购专员': (7000, 12000),
        '采购助理': (5000, 8000),
        '法务总监': (30000, 50000),
        '法务经理': (20000, 35000),
        '法务专员': (10000, 18000),
    }
    
    salaries = []
    for emp_name, emp_id in emp_map.items():
        cursor.execute('SELECT position FROM employees WHERE emp_id = ?', (emp_id,))
        position = cursor.fetchone()[0]
        
        min_salary, max_salary = salary_rules.get(position, (8000, 15000))
        base_salary = random.randint(min_salary, max_salary)
        bonus = random.randint(0, int(base_salary * 0.3))
        
        salaries.append((emp_id, base_salary, bonus, '2024-01-01'))
    
    cursor.executemany('''
        INSERT INTO salaries (emp_id, base_salary, bonus, effective_date)
        VALUES (?, ?, ?, ?)
    ''', salaries)
    
    conn.commit()


def main():
    """主函数"""
    
    # 连接数据库（如果不存在会自动创建）
    conn = sqlite3.connect(DATABASE_PATH)
    
    create_tables(conn)
    insert_sample_data(conn)
    
    # VACUUM需要在事务外执行
    conn.commit()
    conn.execute('VACUUM')
    conn.close()

    print(f"\n数据库初始化完成: {DATABASE_PATH}")
    print(f"数据已重置，ID从1开始")


if __name__ == '__main__':
    main()
