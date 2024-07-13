import os
import sqlite3
import platform
import numpy as np
from scipy.stats import shapiro, spearmanr, mannwhitneyu, pearsonr
import matplotlib.pyplot as plt
from datetime import datetime

class Graphs:

    def __init__(self, fast: bool = False):
        # Path do script
        BASE_DIR = os.path.dirname(os.path.abspath(__file__))
        
        # Conectando ao banco local
        path_local_db = os.path.join(BASE_DIR, self.env("RESEARCH_DB"))
        self.conn_local_db = sqlite3.connect(path_local_db)
        self.local_db = self.conn_local_db.cursor()
    
    # Acessa as envs    
    def env(self, var):
        env = '\\.env'
        print(platform.system())
        if(platform.system() in ['Linux', 'Darwin']):
            env = '/.env'
            
        with open(os.path.dirname(os.path.realpath(__file__)) + env, 'r', encoding='utf-8') as file_env:
            line = file_env.readline()
            while(line):
                content = line.split('=')
                if(content[0] == var):
                    return content[1]
                line = file_env.readline()

    # Pega uma coluna da base de dados construida
    def get_one_smell(self, smell):
        self.local_db.execute(f"""
            SELECT DISTINCT
                project_id,
                author,
                code_smell,
                percentage
            FROM
                author_code_smells_final
            WHERE code_smell = {smell}
        """)
            
        array = []
        for result in self.local_db.fetchall():
            if result[3] == None:
                array.append(0)
            else:
                array.append(result[2])

        return np.array(array)

    # Pega 2 colunas da base de dados construida, r = round
    def get_columns(self, x, y, r=False):
        self.local_db.execute(f"""
                SELECT DISTINCT
                    project_id,
                    author,
                    code_smell,
                    percentage
                FROM
                    author_code_smells_final
                WHERE
                    code_smell = '{x}' OR code_smell = '{y}'
            """)
        
        x = []
        y = []
        for result in self.local_db.fetchall():
            column_x = 0
            column_y = 0
            
            if(x == result[2] and result[3] != None):
                column_x = result[3]
            if(y == result[2] and result[3] != None):
                column_y = result[3]

            if(r):
                column_x = round(column_x)
                column_y = round(column_y)
    
            x.append(column_x)
            y.append(column_y)
            
        return (np.array(x), np.array(y))

    # Pearson
    def pearson(self, x, y, plot=True):
        column_x = x
        column_y = y
        
        x, y = self.get_columns(x, y)

        # Calcular o coeficiente de correlação de Pearson
        corr_coef, p_value = pearsonr(x, y)

        if(plot):
            # Plotar o gráfico de dispersão
            plt.scatter(x, y)
            plt.title(f'Gráfico de Dispersão: {column_x} VS {column_y} (Pearson)')
            plt.xlabel(column_x)
            plt.ylabel(column_y)

            # Imprimir o coeficiente de correlação de Pearson
            print("Coeficiente de correlação de Pearson:", corr_coef)
            plt.text(0, -0.25, "Coeficiente de correlação de Pearson: {}".format(corr_coef),
                    bbox=dict(facecolor='red', alpha=0.5))
            plt.savefig('../figures/{}_pearson_{}X{}.png'.format(datetime.now().strftime("%Y%m%d%H%M%S"),column_x,column_y))
        
            plt.show()
        return (corr_coef, p_value)

    # Spearman
    def spearman(self, x, y, plot=True):
        column_x = x
        column_y = y
        x, y = self.get_columns(x, y)
        
        # Calcular o coeficiente de correlação de Spearman
        corr_coef, p_value = spearmanr(x, y)
        if(plot):
            # Plotar o gráfico de dispersão
            plt.scatter(x, y)
            plt.title(f'Gráfico de Dispersão: {column_x} VS {column_y} (Spearman)')
            plt.xlabel(column_x)
            plt.ylabel(column_y)

            # Imprimir o coeficiente de correlação de Spearman
            print("Coeficiente de correlação de Spearman:", corr_coef)
            print("p-value", p_value)
            plt.text(0, -0.25, "Coeficiente de correlação de Spearman: {}".format(corr_coef),
            bbox=dict(facecolor='red', alpha=0.5))
            plt.savefig('../figures/{}_spearman_{}X{}.png'.format(datetime.now().strftime("%Y%m%d%H%M%S"),column_x,column_y))
        
            plt.show()
        return (corr_coef, p_value)

    # Gráfico de dispersão normal
    def scatter(self, x, y):
        column_x = x
        column_y = y
        x, y = self.get_columns(x, y)

        # Plotar o gráfico de dispersão
        plt.scatter(x, y)
        plt.title(f'Gráfico de Dispersão: {column_x} VS {column_y}')
        plt.xlabel(column_x)
        plt.ylabel(column_y)
        plt.savefig('../figures/{}_scatter_{}X{}.png'.format(datetime.now().strftime("%Y%m%d%H%M%S"),column_x,column_y))
        plt.show()
        
    def new_shapiro(self, column):
        data = self.get_one_column(column)
        statistic, p_value = shapiro(data)
        
        fig, ax = plt.subplots()

        if p_value > 0.05:
            ax.set_title('Distribuição normal (p={:.3f})'.format(p_value))
            ax.hist(data, bins='auto', alpha=0.7, color='blue', edgecolor='black')
        else:
            ax.set_title('Distribuição não-normal (p={:.3f})'.format(p_value))
            ax.hist(data, bins='auto', alpha=0.7, color='red', edgecolor='black')

        plt.show()
    
    def new_mann(self, x, y):
        column_x = x
        column_y = y
        x, y = self.get_columns(x, y)
        
        statistic, p_value = mannwhitneyu(x, y)
        fig, ax = plt.subplots()

        if p_value > 0.05:
            ax.set_title('Distribuições semelhantes (p={:.3f})'.format(p_value))
            color = 'blue'
        else:
            ax.set_title('Distribuições diferentes (p={:.3f})'.format(p_value))
            color = 'red'

        ax.hist(column_x, bins='auto', alpha=0.7, color=color, edgecolor='black', label='Data 1')
        ax.hist(column_y, bins='auto', alpha=0.7, color=color, edgecolor='black', linestyle='dashed', label='Data 2')
        ax.legend(loc='upper right')

        plt.show()
    
    def get_all_columns(self):
        self.local_db.execute("SELECT DISTINCT code_smell FROM project_code_smells_final")
        columns = []
        for row in self.local_db.fetchall():
            columns.append(row[0])
        return columns

if __name__ == "__main__":
    
    graph = Graphs()
    
    while True:
        print("\n\n--------------------------------------------------------------------------------")
        choose = int(input("""
            - Qual função você deseja acessar?
            1. Pearson
            2. Spearman
            3. Mann-Whitney U
            4. Shapiro
            5. Dispersão comum
        >> """))
        
        print("\n Colunas disponíveis: \n")
        columns = graph.get_all_columns()
        print(columns)
        
        i = 0
        for column in columns:
            print(i," - ", column, '\n')
            i += 1
        
        
        if choose < 0:
            print("\n\nPor favor, escolha uma opção válida.")
        else:

            if choose == 4:
                column = str(input("\n >> Digite a coluna que deseja aplicar o método (número ou nome): "))
                
                if(column.isdigit() and int(column) < len(columns)):
                    graph.new_shapiro(columns[int(column)])
                elif column in columns:
                    graph.new_shapiro(column)
                else:
                    print("\n Essa coluna não exite!")

            elif choose in [1, 2, 3, 5]:
                x = str(input("\n>> Digite a coluna que será o X: "))
                y = str(input(">> Digite a coluna que será o Y: "))
                
                if(x.isdigit() and y.isdigit() and int(x) < len(columns) and int(y) < len(columns)):
                    if choose == 1:
                        graph.pearson(columns[int(x)], columns[int(y)])
                    elif choose == 2:
                        graph.spearman(columns[int(x)], columns[int(y)])
                    elif choose == 3:
                        graph.new_mann(columns[int(x)], columns[int(y)])
                    elif choose == 5:
                        graph.scatter(columns[int(x)], columns[int(y)])
                        
                elif(x not in columns or y not in columns):
                    print("\n Coluna inexistente!")
                elif choose == 1:
                    graph.pearson(x, y)
                elif choose == 2:
                    graph.spearman(x, y)
                elif choose == 3:
                    graph.new_mann(x, y)
                elif choose == 5:
                    graph.scatter(x, y)
        
        ex = str(input(" - Deseja realizar outra operação? (S/n):"))
        if(ex == 'n' or ex == 'N'):
            exit()