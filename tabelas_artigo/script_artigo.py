import os
from datetime import datetime
import sqlite3
import platform

class Research:

    def __init__(self, fast: bool = True):
        # Path do script
        BASE_DIR = os.path.dirname(os.path.abspath(__file__))

        # Conectando ao banco de dados do https://github.com/clowee/The-Technical-Debt-Data_set/
        # path_data_set = os.path.join(BASE_DIR, "dataset.db")
        conn_data_set = sqlite3.connect("C:/Users/gcmor/Desktop/td_V2.db")
        self.dataset = conn_data_set.cursor()
        
        # Conectando ao banco local
        path_local_db = os.path.join(BASE_DIR, self.env("RESEARCH_DB"))
        self.conn_local_db = sqlite3.connect(path_local_db)
        self.local_db = self.conn_local_db.cursor()

        # Caso deseje pular a etapa de verificação de leitura e gravação dos projetos e autores 
        if (not fast):
            pass
            self.init_local_table()

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
        
###########################################################################################

    def create_raw_data_table(self):
        self.local_db.execute("""
            CREATE TABLE IF NOT EXISTS "raw_data" (
                "project_id" TEXT,
                "author" TEXT,
                "code_smells" INTEGER,
                "lines_edited" INTEGER,
                "commits" INTEGER,
                "sonar_smells" INTEGER
            );
        """)
        self.conn_local_db.commit()

        # Insere os dados na tabela
        self.local_db.execute("""
            INSERT INTO raw_data (project_id, author, code_smells, lines_edited, commits, sonar_smells)
            SELECT
                project_id,
                author,
                SUM(amount_code_smells) AS code_smells,
                SUM(number_lines_edited) AS lines_edited,
                SUM(amount_commits) AS commits,
                SUM(amount_sonar_smells) AS sonar_smells
            FROM author_information
            WHERE
                amount_code_smells IS NOT NULL AND
                number_lines_edited IS NOT NULL AND
                amount_commits IS NOT NULL AND
                amount_sonar_smells IS NOT NULL
            GROUP BY project_id, author
        """)
        self.conn_local_db.commit()

    # Função para criar tabelas com filtros de commits
    def create_normalized_table(self, min_commits):
        self.local_db.execute(f"""
            CREATE TABLE IF NOT EXISTS "normalized_author_summary_{min_commits}" (
                "project_id" INTEGER,
                "author" TEXT,
                "code_smells" REAL,
                "lines_edited" REAL,
                "commits" REAL,
                "sonar_smells" REAL
            );
        """)
        self.conn_local_db.commit()

        query = f"""
            SELECT
                ai.project_id,
                ai.author,
                (ai.amount_code_smells * 100.0 / pi.amount_code_smells) AS code_smells_percentage,
                (ai.number_lines_edited * 100.0 / pi.number_lines_edited) AS lines_edited_percentage,
                (ai.amount_commits * 100.0 / pi.amount_commits) AS commits_percentage,
                (ai.amount_sonar_smells * 100.0 / pi.amount_sonar_smells) AS sonar_smells_percentage,
                ai.amount_commits AS commits
            FROM
                author_information ai
            JOIN
                project_information pi
            ON
                ai.project_id = pi.project_id
            WHERE
                ai.amount_commits >= {min_commits} AND
                ai.amount_code_smells IS NOT NULL AND
                pi.amount_code_smells IS NOT NULL AND
                ai.number_lines_edited IS NOT NULL AND
                pi.number_lines_edited IS NOT NULL AND
                ai.amount_commits IS NOT NULL AND
                pi.amount_commits IS NOT NULL AND
                ai.amount_sonar_smells IS NOT NULL AND
                pi.amount_sonar_smells IS NOT NULL;
        """
        data = self.local_db.execute(query).fetchall()

        results = []
        for row in data:
            project_id = row[0]
            author = row[1]
            code_smells = row[2]
            lines_edited = row[3]
            commits = row[4]
            sonar_smells = row[5]

            results.append((
                project_id,
                author,
                code_smells,
                lines_edited,
                commits,
                sonar_smells
            ))

        self.local_db.executemany(f"""
            INSERT INTO normalized_author_summary_{min_commits}
            (project_id, author, code_smells, lines_edited, commits, sonar_smells)
            VALUES (?, ?, ?, ?, ?, ?)
        """, results)
        self.conn_local_db.commit()

    def create_normalized_separated_by_author_avg(self):
        # Cria a tabela para armazenar os resultados da média
        self.local_db.execute("""
            CREATE TABLE IF NOT EXISTS "normalized_separated_by_author_avg" (
                "author" TEXT PRIMARY KEY,
                "code_smells" REAL,
                "lines_edited" REAL,
                "commits" REAL,
                "sonar_smells" REAL
            );
        """)
        self.conn_local_db.commit()

        # Consulta SQL para calcular a média e inserir na nova tabela
        query = """
            INSERT INTO normalized_separated_by_author_avg (author, code_smells, lines_edited, commits,
                                            sonar_smells)
            SELECT
                author,
                AVG(code_smells) AS code_smells,
                AVG(lines_edited) AS lines_edited,
                AVG(commits) AS commits,
                AVG(sonar_smells) AS sonar_smells
            FROM
                normalized_author_summary_0
            GROUP BY
                author;
        """

        # Executa a consulta e insere os dados na nova tabela
        self.local_db.execute(query)
        self.conn_local_db.commit()

# Main do script
if __name__ == "__main__":
    research = Research(fast=True)
    
    # Incialização do data_set
    research.init_local_table()
    research.calculate_author_infos()
    research.calculate_project_infos()
    research.read_amout_sonar_smells_author()
    research.read_amout_sonar_smells_project()
    research.read_amout_code_smells_author()
    research.read_amout_code_smells_project()
    research.read_number_lines_edited_author()
    research.read_number_lines_edited_project()

    # Tabela de dados brutos
    research.create_raw_data_table()
    
    # Tabela atributos normalizados
    # Cria tabelas para diferentes valores de commits
    research.create_normalized_table(0)
    research.create_normalized_table(2)
    research.create_normalized_table(4)
    research.create_normalized_table(5)
    research.create_normalized_separated_by_author_avg()