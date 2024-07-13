import os
from datetime import datetime
import sqlite3
import platform

class Research:

    def __init__(self, fast: bool = True):
        # Path do script
        BASE_DIR = os.path.dirname(os.path.abspath(__file__))

        # Conectando ao banco de dados do https://github.com/clowee/The-Technical-Debt-Data_set/
        path_data_set = os.path.join(BASE_DIR, self.env("DATASET"))
        conn_data_set = sqlite3.connect(path_data_set)
        self.dataset = conn_data_set.cursor()
        
        # Conectando ao banco local
        path_local_db = os.path.join(BASE_DIR, self.env("RESEARCH_DB"))
        self.conn_local_db = sqlite3.connect('path_local_db')
        self.local_db = self.conn_local_db.cursor()

        # Caso deseje pular a etapa de verificação de leitura e gravação dos projetos e autores 
        if (not fast):
            pass
            # self.init_local_table()

    # def env(self, var):
    #     env = '\\.env'
    #     if(platform.system() in ['Linux', 'Darwin']):
    #         env = '/.env'
            
    #     with open(os.path.dirname(os.path.realpath(__file__)) + env, 'r', encoding='utf-8') as file_env:
    #         line = file_env.readline()
    #         while(line):
    #             content = line.split('=')
    #             if(content[0] == var):
    #                 return content[1].replace('\n', '')
    #             line = file_env.readline()
    
    def env(sefl, var):
        env = '\\.env'
        if(platform.system() in ['Linux', 'Darwin']):
            env = '/.env'
            
        with open(os.path.dirname(os.path.realpath(__file__)) + env, 'r', encoding='utf-8') as file_env:
            line = file_env.readline()
            while(line):
                content = line.split('=')
                if(content[0] == var):
                    return content[1].replace('\n', '')
                line = file_env.readline()
    # Fecha as conexões
    def close_connections(self):
        self.dataset.close()
        self.local_db.close()

    # Cria a tabela que é armazendo os dados caso não exista
    def init_local_table(self):
        self.local_db.execute("""
                CREATE TABLE IF NOT EXISTS "author_information" (
                    "project_id"                      TEXT,
                    "author"	                      TEXT,
                    "project_experience_in_days"      REAL,
                    "project_experience_in_hours"     REAL,
                    "number_lines_edited"	          INTEGER,
                    "single_commit"                   INTEGER,
                    "amount_commits"		          INTEGER,
                    "first_commit"                    TEXT,
                    "last_commit"                     TEXT,
                    "amount_code_smells"	          INTEGER,
                    "amount_sonar_smells"	          INTEGER
                    );
            """)
        
        self.local_db.execute("""
                CREATE TABLE IF NOT EXISTS "author_percentage_information" (
                    "project_id"                                TEXT,
                    "author"	                                TEXT,
                    "lines_edited"                   REAL,
                    "rounded_lines_edited"           REAL,
                    "commits"                        REAL,
                    "rounded_commits"                REAL,
                    "experience_in_days"             REAL,
                    "rounded_experience_in_days"     REAL,
                    "experience_in_hours"            REAL,
                    "rounded_experience_in_hours"    REAL,
                    "code_smells"                    REAL,
                    "rounded_code_smells"            REAL,
                    "sonar_smells"                   REAL,
                    "rounded_sonar_smells"           REAL
                    
                );
            """)

        self.local_db.execute("""
            CREATE TABLE IF NOT EXISTS "project_information" (
                "project_id"            TEXT,
                "amount_commits"		INTEGER,
                "first_commit"          TEXT,
                "last_commit"           TEXT,
                "total_time_in_days"    REAL,
                "total_time_in_hours"   REAL,
                "number_lines_edited"	INTEGER,
                "amount_code_smells"	INTEGER,
                "amount_sonar_smells"	INTEGER
                );
            """)
        self.conn_local_db.commit()
        self.insert_authors_and_projects()

    # Insere todos os projetos e autores no banco de dados local
    def insert_authors_and_projects(self):
        self.dataset.execute("SELECT project_id, author FROM git_commits")

        for result in self.dataset.fetchall():
            project_id = result[0]
            author = result[1]
            # Inserindo os projetos e os autores na tabela que guarda as informações dos autores
            self.local_db.execute("SELECT 1 FROM author_information WHERE project_id = ? AND author = ?", (project_id, author))
            if (len(self.local_db.fetchall()) == 0):
                self.local_db.execute("INSERT INTO author_information (project_id, author) VALUES (?,?)", (project_id, author))
            
            # Inserindo os projetos e os autores na tabela que guarda as informações de porcentagem dos autores
            self.local_db.execute("SELECT 1 FROM author_percentage_information WHERE project_id = ? AND author = ?", (project_id, author))
            if (len(self.local_db.fetchall()) == 0):
                self.local_db.execute("INSERT INTO author_percentage_information (project_id, author) VALUES (?,?)", (project_id, author))

            # Inserindo os projetos na tabela que guarda as informações dos projetos
            self.local_db.execute("SELECT 1 FROM project_information WHERE project_id = ?", (project_id,))
            if (len(self.local_db.fetchall()) == 0):
                self.local_db.execute("INSERT INTO project_information (project_id) VALUES (?)", (project_id,))

        self.conn_local_db.commit()
        
    # Lê o Data Set e grava no banco local a quantidade de sonar smells para cada dev
    def read_amout_sonar_smells_author(self):
        self.dataset.execute("""
            SELECT
                COUNT(DISTINCT si.issue_key) AS amount_sonar_smells,
                gc.project_id,
                gc.author
            FROM 
                git_commits AS gc
            INNER JOIN 
                sonar_analysis AS sa ON gc.commit_hash = sa.revision
            INNER JOIN 
                sonar_issues AS si ON sa.analysis_key = si.creation_analysis_key
            WHERE
                gc.merge = 'False' 
                AND si.type = 'CODE_SMELL' 
            GROUP BY gc.project_id, gc.author
        """)

        for result in self.dataset.fetchall():
            print("Updating amout sonar smells to: ", result)
            self.local_db.execute(
                """
                    UPDATE 
                        author_information 
                    SET 
                        amount_sonar_smells = ?
                    WHERE 
                        project_id = ? 
                        AND author = ?
                """,
                (result)
            )
        self.conn_local_db.commit()
        
    # Lê o Data Set e grava no banco local a quantidade de sonar smells para cada projeto
    def read_amout_sonar_smells_project(self):
        self.dataset.execute("""
            SELECT
                COUNT(DISTINCT si.issue_key) AS amount_sonar_smells,
                gc.project_id
            FROM 
                git_commits AS gc
            INNER JOIN 
                sonar_analysis AS sa ON gc.commit_hash = sa.revision
            INNER JOIN 
                sonar_issues AS si ON sa.analysis_key = si.creation_analysis_key
            WHERE
                gc.merge = 'False' 
                AND si.type = 'CODE_SMELL'  
            GROUP BY gc.project_id
        """)

        for result in self.dataset.fetchall():
            print("Updating amout sonar smells to: ", result)
            self.local_db.execute(
                """
                    UPDATE 
                        project_information 
                    SET 
                        amount_sonar_smells = ?
                    WHERE 
                        project_id = ? 
                """,
                (result)
            )
        self.conn_local_db.commit()

    # Lê o Data Set e grava no banco local a quantidade de code smells para cada dev
    def read_amout_code_smells_author(self):
        self.dataset.execute("""
            SELECT
                COUNT(DISTINCT si.issue_key) AS amount_code_smells,
                gc.project_id,
                gc.author
            FROM 
                git_commits AS gc
            INNER JOIN 
                sonar_analysis AS sa ON gc.commit_hash = sa.revision
            INNER JOIN 
                sonar_issues AS si ON sa.analysis_key = si.creation_analysis_key
            WHERE
                gc.merge = 'False' 
                AND si.rule LIKE 'code_smells:%' 
            GROUP BY gc.project_id, gc.author
        """)

        for result in self.dataset.fetchall():
            print("Updating amout code smells to: ", result)
            self.local_db.execute(
                """
                    UPDATE 
                        author_information 
                    SET 
                        amount_code_smells = ?
                    WHERE 
                        project_id = ? 
                        AND author = ?
                """,
                (result)
            )
        self.conn_local_db.commit()

    # Lê o Data Set e grava no banco local a quantidade de code smells para cada projeto
    def read_amout_code_smells_project(self):
        self.dataset.execute("""
            SELECT
                COUNT(DISTINCT si.issue_key) AS amount_code_smells,
                gc.project_id
            FROM 
                git_commits AS gc
            INNER JOIN 
                sonar_analysis AS sa ON gc.commit_hash = sa.revision
            INNER JOIN 
                sonar_issues AS si ON sa.analysis_key = si.creation_analysis_key
            WHERE
                gc.merge = 'False' 
                AND si.rule LIKE 'code_smells:%' 
            GROUP BY gc.project_id
        """)

        for result in self.dataset.fetchall():
            print("Updating amout code smells to: ", result)
            self.local_db.execute(
                """
                    UPDATE 
                        project_information 
                    SET 
                        amount_code_smells = ?
                    WHERE 
                        project_id = ? 
                """,
                (result)
            )
        self.conn_local_db.commit()

    # Lê o Data Set e grava no banco local a quantidade de linhas editadas para cada dev
    def read_number_lines_edited_author(self):
        self.dataset.execute("""
            SELECT
                (SUM(lines_added) + SUM(lines_removed)) as number_lines_edited,
                git_commits.project_id,
                git_commits.author
            FROM git_commits
            INNER JOIN
                git_commits_changes ON git_commits.commit_hash = git_commits_changes.commit_hash
            WHERE
                git_commits.merge = 'False' 
            GROUP BY git_commits.project_id, git_commits.author
        """)

        for result in self.dataset.fetchall():
            print("Updating number lines edited to: ", result)
            self.local_db.execute(
                """
                    UPDATE 
                        author_information 
                    SET 
                        number_lines_edited = ?
                    WHERE 
                        project_id = ? 
                        AND author = ?
                """,
                (result)
            )
        self.conn_local_db.commit()

    # Lê o Data Set e grava no banco local a quantidade de linhas editadas para cada projeto
    def read_number_lines_edited_project(self):
        self.dataset.execute("""
            SELECT
                (SUM(gcc.lines_added) + SUM(gcc.lines_removed)) as number_lines_edited,
                gcc.project_id
            FROM 
                git_commits_changes gcc
            INNER JOIN 
                git_commits gc ON gc.commit_hash = gcc.commit_hash
            WHERE
                gc.merge = 'False' 
            GROUP BY gcc.project_id
        """)

        for result in self.dataset.fetchall():
            print("Updating number lines edited to: ", result)
            self.local_db.execute(
                """
                    UPDATE 
                        project_information 
                    SET 
                        number_lines_edited = ?
                    WHERE 
                        project_id = ? 
                """,
                (result)
            )
        self.conn_local_db.commit()
    
    # Pega o primeiro commit e o último de cada author em cada projeto e calcula algumas informações
    def calculate_author_infos(self):
        self.dataset.execute("""
            SELECT DISTINCT
                project_id,
                author,
                MIN(author_date) as first_commit,
                MAX(author_date) as last_commit,
                COUNT(DISTINCT commit_hash) as amount_commits
            FROM 
                git_commits
            WHERE 
                merge='False'
            GROUP BY project_id, author
        """)

        for result in self.dataset.fetchall():
            project_id = result[0]
            author = result[1]
            first_commit = result[2].replace('Z', '+00:00').replace('T', ' ')
            last_commit = result[3].replace('Z', '+00:00').replace('T', ' ')
            amount_commits = result[4]
            single_commit = 0
            
            date_format = '%Y-%m-%d %H:%M:%S%z'
            first_date = datetime.strptime(first_commit, date_format)
            last_date = datetime.strptime(last_commit, date_format)
            delta = last_date - first_date
            days = delta.days
            hours = round((delta.total_seconds() / 3600), 2)

            if(first_date == last_date):
                single_commit = 1
            
            print("Updating project experience to project_id {} author {}".format(project_id, author))
            self.local_db.execute(
                """
                    UPDATE 
                        author_information
                    SET 
                        project_experience_in_days = ?,
                        project_experience_in_hours = ?,
                        single_commit = ?,
                        first_commit = ?,
                        last_commit = ?,
                        amount_commits = ?
                    WHERE 
                        project_id = ?
                        AND author = ?
                """,
                (days, hours, single_commit, first_date, last_date, amount_commits, project_id, author)
            )
        self.conn_local_db.commit()

    # Pega o primeiro commit e o último de cada projeto e calcula a diferença
    def calculate_project_infos(self):
        self.dataset.execute("""
            SELECT DISTINCT
                project_id,
                MIN(author_date) as first_commit,
                MAX(author_date) as last_commit,
                COUNT(DISTINCT commit_hash) as amount_commits
            FROM 
                git_commits
            WHERE 
                merge='False'
            GROUP BY project_id
        """)

        for result in self.dataset.fetchall():
            project_id = result[0]
            first_commit = result[1].replace('Z', '+00:00').replace('T', ' ')
            last_commit = result[2].replace('Z', '+00:00').replace('T', ' ')
            amount_commits = result[3]
            
            date_format = '%Y-%m-%d %H:%M:%S%z'
            first_date = datetime.strptime(first_commit, date_format)
            last_date = datetime.strptime(last_commit, date_format)
            delta = last_date - first_date
            days = delta.days
            hours = round((delta.total_seconds() / 3600), 2)
            
            self.local_db.execute(
                """
                    UPDATE 
                        project_information
                    SET 
                        total_time_in_days = ?,
                        total_time_in_hours = ?,
                        first_commit = ?,
                        last_commit = ?,
                        amount_commits = ?
                    WHERE 
                        project_id = ?
                """,
                (days, hours, first_date, last_date, amount_commits, project_id)
            )
        self.conn_local_db.commit()

    # Deleta authores que não tem nada em projeto nenhum
    def delete_null_authors(self):
        self.local_db.execute("""
            DELETE FROM 
                author_information
            WHERE
                project_experience_in_days is NULL 
                AND project_experience_in_hours is NULL 
                AND number_lines_edited is NULL 
                AND single_commit is NULL 
                AND first_commit is NULL 
                AND last_commit is NULL 
                AND amount_code_smells is NULL 
                AND amount_sonar_smells is NULL 
        """)
        self.conn_local_db.commit()
        
    # Calcula a porcentagem de linhas editadas de cada author
    def percentage_lines_edited(self):
        self.local_db.execute("""
            SELECT DISTINCT
                a.project_id,
                a.author,
                a.number_lines_edited,
                p.number_lines_edited as project_number_lines_edited
            FROM 
                author_information a
            INNER JOIN
                project_information p ON p.project_id = a.project_id
        """)

        for result in self.local_db.fetchall():
            project_id = result[0]
            author = result[1]
            number_lines_edited = result[2]
            project_number_lines_edited = result[3]
            lines_edited = None
            rounded_lines_edited = None
            
            if(number_lines_edited != 0 and number_lines_edited != None):
                lines_edited = ((number_lines_edited * 100) / project_number_lines_edited)
                rounded_lines_edited = round(lines_edited, 2)

            print("Updating lines_edited to project_id {} author {}".format(project_id, author))
            self.local_db.execute(
                """
                    UPDATE 
                        author_percentage_information
                    SET 
                        lines_edited = ?,
                        rounded_lines_edited = ?
                    WHERE 
                        project_id = ?
                        AND author = ?
                """,
                (lines_edited, rounded_lines_edited, project_id, author)
            )
        self.conn_local_db.commit()
        
    # Calcula a porcentagem de commits de cada author
    def percentage_commits(self):
        self.local_db.execute("""
            SELECT DISTINCT
                a.project_id,
                a.author,
                a.amount_commits,
                p.amount_commits as project_amount_commits
            FROM 
                author_information a
            INNER JOIN
                project_information p ON p.project_id = a.project_id
        """)

        for result in self.local_db.fetchall():
            project_id = result[0]
            author = result[1]
            amount_commits = result[2]
            project_amount_commits = result[3]
            
            commits = None
            rounded_commits = None
            
            if(amount_commits != 0 and amount_commits != None):
                commits = ((amount_commits * 100) / project_amount_commits)
                rounded_commits = round(commits, 2)

            print("Updating commits to project_id {} author {}".format(project_id, author))
            
            self.local_db.execute(
                """
                    UPDATE 
                        author_percentage_information
                    SET 
                        commits = ?,
                        rounded_commits = ?
                    WHERE 
                        project_id = ?
                        AND author = ?
                """,
                (commits, rounded_commits, project_id, author)
            )
        self.conn_local_db.commit()

    # Calcula a porcentagem de experiencia de cada author
    def percentage_experience(self):
        self.local_db.execute("""
            SELECT DISTINCT
                a.project_id,
                a.author,
                a.project_experience_in_days,
                a.project_experience_in_hours,
                p.total_time_in_days,
                p.total_time_in_hours
            FROM 
                author_information a
            INNER JOIN
                project_information p ON p.project_id = a.project_id
        """)

        for result in self.local_db.fetchall():
            project_id = result[0]
            author = result[1]
            project_experience_in_days = result[2]
            project_experience_in_hours = result[3]
            total_time_in_days = result[4]
            total_time_in_hours = result[5]
            
            experience_in_days = None
            rounded_experience_in_days = None
            
            experience_in_hours = None
            rounded_experience_in_hours = None

            if(project_experience_in_days != 0 and project_experience_in_days != None):
                experience_in_days = ((project_experience_in_days * 100) / float(total_time_in_days))
                rounded_experience_in_days = round(experience_in_days, 2)
                
            if(project_experience_in_hours != 0 and project_experience_in_hours != None):
                experience_in_hours = ((project_experience_in_hours * 100) / float(total_time_in_hours))
                rounded_experience_in_hours = round(experience_in_hours, 2)

            print("Updating percentage_experience to project_id {} author {}".format(project_id, author))
            
            self.local_db.execute(
                """
                    UPDATE 
                        author_percentage_information
                    SET 
                        experience_in_days = ?,
                        rounded_experience_in_days = ?,
                        experience_in_hours = ?,
                        rounded_experience_in_hours = ?
                    WHERE 
                        project_id = ?
                        AND author = ?
                """,
                (experience_in_days, rounded_experience_in_days, experience_in_hours, rounded_experience_in_hours, project_id, author)
            )
        self.conn_local_db.commit()
        
    # Porcentagem de code smells
    def percentage_smells(self):
        self.local_db.execute("""
            SELECT DISTINCT
                a.project_id,
                a.author,
                a.amount_code_smells,
                a.amount_sonar_smells,
                p.amount_code_smells AS project_amount_code_smells,
                p.amount_sonar_smells AS project_amount_sonar_smells
            FROM 
                author_information a
            INNER JOIN
                project_information p ON p.project_id = a.project_id
        """)

        for result in self.local_db.fetchall():
            project_id = result[0]
            author = result[1]
            amount_code_smells = result[2]
            amount_sonar_smells = result[3]
            project_amount_code_smells = result[4]
            project_amount_sonar_smells = result[5]
            
            code_smells = None
            rounded_code_smells = None
            
            sonar_smells = None
            rounded_sonar_smells = None
            
            if(amount_code_smells != 0 and amount_code_smells != None):
                code_smells = ((amount_code_smells * 100) / project_amount_code_smells)
                rounded_code_smells = round(code_smells, 2)
            
            if(amount_sonar_smells != 0 and amount_sonar_smells != None):
                sonar_smells = ((amount_sonar_smells * 100) / project_amount_sonar_smells)
                rounded_sonar_smells = round(sonar_smells, 2)

            print("Updating smells to project_id {} author {}".format(project_id, author))
            
            self.local_db.execute(
                """
                    UPDATE 
                        author_percentage_information
                    SET 
                        code_smells = ?,
                        rounded_code_smells = ?,
                        sonar_smells = ?,
                        rounded_sonar_smells = ?
                    WHERE 
                        project_id = ?
                        AND author = ?
                """,
                (code_smells, rounded_code_smells, sonar_smells, rounded_sonar_smells, project_id, author)
            )
        self.conn_local_db.commit()

    # Deleta authores que não tem nada em projeto nenhum
    def delete_null_authors_percentage(self):
        self.local_db.execute("""
            DELETE FROM 
                author_percentage_information
            WHERE
                lines_edited is NULL
                AND commits is NULL
                AND experience_in_days is NULL
                AND experience_in_hours is NULL
        """)
        self.conn_local_db.commit()

    def init_code_smells_table(self):
        self.local_db.execute("""
            CREATE TABLE IF NOT EXISTS "author_code_smells_final" (
                "project_id"    TEXT,
                "author"	    TEXT,
                "code_smell"    TEXT,
                "amount"        INTEGER,
                "percentage"    REAL
            );
    """)

    def init_project_code_smells_table(self):
        self.local_db.execute("""
            CREATE TABLE IF NOT EXISTS "project_code_smells_final" (
                "project_id"    TEXT,
                "code_smell"    TEXT,
                "amount"        INTEGER,
                "percentage"    REAL
            );
    """)
    
    def read_type_code_smell(self):
        self.dataset.execute("""
            SELECT DISTINCT
                gc.project_id,
                gc.author,
                si.rule as code_smell,
                COUNT(si.rule) as amount
            FROM 
                git_commits AS gc
            INNER JOIN 
                sonar_analysis AS sa ON gc.commit_hash = sa.revision
            INNER JOIN 
                sonar_issues AS si ON sa.analysis_key = si.creation_analysis_key
            WHERE
                gc.merge = 'False' 
                AND si.rule LIKE 'code_smells:%' 
            GROUP BY gc.project_id, gc.author, si.rule
        """)

        for result in self.dataset.fetchall():
            print("Insert into code_smell: ", result)
            self.local_db.execute(
                """
                    INSERT INTO
                        author_code_smells_final (project_id, author, code_smell, amount)
                    VALUES 
                        (?, ?, ?, ?)
                """,
                (result)
            )
        self.conn_local_db.commit()
        
    def read_type_project_code_smell(self):
        self.dataset.execute("""
            SELECT DISTINCT
                gc.project_id,
                si.rule as code_smell,
                COUNT(si.rule) as amount
            FROM 
                git_commits AS gc
            INNER JOIN 
                sonar_analysis AS sa ON gc.commit_hash = sa.revision
            INNER JOIN 
                sonar_issues AS si ON sa.analysis_key = si.creation_analysis_key
            WHERE
                gc.merge = 'False' 
                AND si.rule LIKE 'code_smells:%' 
            GROUP BY gc.project_id, si.rule
        """)

        for result in self.dataset.fetchall():
            print("Insert into project_code_smell: ", result)
            self.local_db.execute(
                """
                    INSERT INTO
                        project_code_smells_final (project_id, code_smell, amount)
                    VALUES 
                        (?, ?, ?)
                """,
                (result)
            )
        self.conn_local_db.commit()
        
    def percentage_type_smell(self):
        self.local_db.execute("""
            SELECT DISTINCT
                pcs.project_id,
                pcs.code_smell,
                pcs.amount,
                (SELECT SUM(pcs2.amount) as amount FROM project_code_smells_final pcs2 WHERE pcs2.project_id = pcs.project_id GROUP BY pcs2.project_id)
            FROM project_code_smells_final pcs
        """)
        result = self.local_db.fetchall()
        for row in result:
            project_id = row[0]
            code_smell = row[1]
            amount = row[2]
            total_amount = row[3]
            
            percentage = ((amount * 100) / total_amount)
            
            self.local_db.execute("""
                UPDATE project_code_smells_final SET percentage = ? WHERE project_id = ? AND code_smell = ?
            """, (percentage, project_id, code_smell))
            
            self.local_db.execute("""
                SELECT DISTINCT
                    acs.author,
                    acs.amount
                FROM author_code_smells_final acs
                WHERE acs.project_id = ? AND acs.code_smell = ?
            """, (project_id, code_smell))
            
            sub_result = self.local_db.fetchall()
            for sub_row in sub_result:
                author = sub_row[0]
                author_amount = sub_row[1]
                
                author_percentage = ((author_amount * 100) / amount)
                
                self.local_db.execute("""
                    UPDATE author_code_smells_final SET percentage = ? WHERE project_id = ? AND code_smell = ? AND author = ?
                """, (author_percentage, project_id, code_smell, author))
            
        self.conn_local_db.commit()
        
# Main do script
if __name__ == "__main__":
    research = Research(fast=True)
    
    # research.read_amout_sonar_smells_author()
    # research.read_amout_sonar_smells_project()
    
    # research.read_amout_code_smells_author()
    # research.read_amout_code_smells_project()

    # research.calculate_author_infos()
    # research.calculate_project_infos()

    # research.read_number_lines_edited_author()
    # research.read_number_lines_edited_project()
    
    # research.delete_null_authors()
    
    # research.percentage_lines_edited()
    # research.percentage_commits()
    # research.percentage_experience()
    # research.percentage_smells()
    
    # research.delete_null_authors_percentage()
    # research.init_code_smells_table()
    # research.read_type_code_smell()
    # research.init_project_code_smells_table()
    # research.read_type_project_code_smell()
    research.percentage_type_smell()
    