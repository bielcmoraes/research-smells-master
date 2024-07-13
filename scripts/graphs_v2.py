import os
import sqlite3
import platform
import numpy as np
import csv
from scipy.stats import shapiro, probplot, spearmanr, mannwhitneyu, pearsonr
# from sklearn.preprocessing import PowerTransformer
import matplotlib.pyplot as plt
# from sklearn.preprocessing import StandardScaler
from datetime import datetime

class Graphs:

    def __init__(self, smell):
        # Path do script
        BASE_DIR = os.path.dirname(os.path.abspath(__file__))
        
        # Conectando ao banco local
        path_local_db = os.path.join(BASE_DIR, smell + "_2_.sqlite")
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
    def get_one_column(self, column):
        self.local_db.execute(f"""
            SELECT DISTINCT
                project_id,
                author,
                {column}
            FROM
                author_percentage_information
            WHERE {column} <> '0'
        """)
            
        array = []
        for result in self.local_db.fetchall():
            if result[2] == None:
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
                    {x},
                    {y}
                FROM
                    author_percentage_information
                WHERE {x} <> '0'
                AND {y} <> '0'
            """)
        
        x = []
        y = []
        for result in self.local_db.fetchall():
            column_x = 0
            column_y = 0
            
            if(result[2] != None):
                column_x = result[2]
            if(result[3] != None):
                column_y = result[3]

            if(r):
                column_x = round(column_x)
                column_y = round(column_y)
    
            x.append(column_x)
            y.append(column_y)
            
        return (np.array(x), np.array(y))
    
    # Shapiro-Wilk somente texto
    def shapiro_text(self, column):
        array = self.get_one_column(column)
        
        stat, p = shapiro(array)
        
        print("SHAPIRO: {}".format(p))
        
        if p > 0.05:
            print(f"{column} são normalmente distribuídas.\n\n")
        else:
            print(f"{column} não são normalmente distribuídas.\n\n")

        # transformer = PowerTransformer(method='yeo-johnson')
        # array_normal = transformer.fit_transform(array.reshape(-1, 1))

        # # scaler = StandardScaler()
        # # array_normal = scaler.fit_transform(array.reshape(-1, 1))

        # stat, p = shapiro(array_normal)

        # print("Power Transformer SHAPIRO: {}".format(p))
        # if p > 0.05:
        #     print(f"{column} normalizadas são normalmente distribuídas.\n\n")
        # else:
        #     print(f"{column} normalizadas não são normalmente distribuídas.\n\n")
    
    # Shapiro-Wilk   
    def shapiro_plot(self, column):
        data = self.get_one_column(column)
        # Realiza o teste Shapiro-Wilk
        stat, p = shapiro(data)

        # Plota o gráfico de probabilidade normal
        fig = plt.figure(figsize=(8, 6))
        ax = fig.add_subplot(111)
        probplot(data, plot=ax)
        ax.set_title(f'Gráfico de probabilidade normal: {column} (Shapiro-Wilk)')
        ax.set_xlabel('Quantis teóricos')
        ax.set_ylabel('Quantis observados')

        # Imprime o resultado do teste Shapiro-Wilk
        print('Estatística de teste:', stat)
        print('Valor p:', p)
        plt.text(0, -12, "Estatística do teste: {}\nValor-p: {}".format(stat, p),
                bbox=dict(facecolor='red', alpha=0.5))
        plt.savefig('../figures/{}_shapiro_{}.png'.format(datetime.now().strftime("%Y%m%d%H%M%S"),column))
        plt.show()
        return (stat, p)
    # Mann-Whitney U
    def mannwhitneyu(self, x, y, plot=True):
        column_x = x
        column_y = y
        x, y = self.get_columns(x, y)

        # Realizar o teste de Mann-Whitney U
        stat, p = mannwhitneyu(x, y)

        if(plot):
            # Plotar os pontos das duas amostras em um gráfico de dispersão
            plt.scatter(x, [0] * len(x), alpha=0.5, label=column_x)
            plt.scatter(y, [1] * len(y), alpha=0.5, label=column_y)
            plt.legend(loc="upper right")
            plt.xlabel(column_x)
            plt.ylabel(column_y)
            plt.title(f"Gráfico de dispersão: {column_x} VS {column_y} (Mann-Whitney U)")

            # Imprimir o resultado do teste no gráfico
            plt.text(0, 0.25, "Estatística do teste: {}\nValor-p: {}".format(stat, p),
                    bbox=dict(facecolor='red', alpha=0.5))
            plt.savefig('../figures/{}_mannwhitneyu_{}X{}.png'.format(datetime.now().strftime("%Y%m%d%H%M%S"),column_x,column_y))
            plt.show()

        return (stat, p)

    # Mann-Whitney U
    def mannwhitneyu_histogram(self, x, y):
        column_x = x
        column_y = y
        x, y = self.get_columns(x, y)

        # Realizar o teste de Mann-Whitney U
        stat, p = mannwhitneyu(x, y)

        # Plotar as duas amostras em um histograma
        plt.hist(x, alpha=0.5, label=column_x)
        plt.hist(y, alpha=0.5, label=column_y)
        plt.legend(loc="upper right")
        plt.xlabel(column_x)
        plt.ylabel(column_y)
        plt.title(f"Histograma das amostras {column_x} VS {column_y} (Mann-Whitney U)")

        # Imprimir o resultado do teste no gráfico
        plt.text(0.5, 20, "Estatística do teste: {}\nValor-p: {}".format(stat, p),
                bbox=dict(facecolor='red', alpha=0.5))
        plt.savefig('../figures/{}_mannwhitneyu_histogram_{}X{}.png'.format(datetime.now().strftime("%Y%m%d%H%M%S"),column_x,column_y))
        plt.show()

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
            plt.text(0, -0.50, "P-value: {}".format(p_value),
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

if __name__ == "__main__":
    
    
    
    all_code_smells = ['code_smells:antisingleton', 'code_smells:baseclass_abstract', 'code_smells:class_data_private', 'code_smells:complex_class', 'code_smells:lazy_class', 'code_smells:long_method', 'code_smells:long_parameter_list', 'code_smells:refused_parent_bequest', 'code_smells:many_field_attributes_not_complex', 'code_smells:spaghetti_code', 'code_smells:speculative_generality', 'code_smells:swiss_army_knife', 'code_smells:large_class']
    i = 0
    for smell in all_code_smells:
        print(i," - ", smell, '\n')
        i += 1
        
    choose_smell = int(input("\n >> Escolha com qual smell você deseja trabalhar: "))
    
    smell_selected = all_code_smells[choose_smell]
    graph = Graphs(smell=smell_selected) 
    while True:
        print("\n\n--------------------------------------------------------------------------------")
        choose = int(input("""
            - Qual função você deseja acessar?
            0. (New) Shapiro-Wilk
            1. Shapiro-Wilk (somente texto)
            2. Shapiro-Wilk
            3. Mann-Whitney U
            4. Mann-Whitney U (histograma)
            5. Pearson
            6. Spearman
            7. Dispersão comum
            8. Todos (coeficiente e p-value)
            9. (New) Mann-Whitney U
            
        >> """))
        
        print("\n Colunas disponíveis: \n")
        columns_all = ["code_smells"]
        # columns_all = ["lines_edited","rounded_lines_edited","commits","rounded_commits","experience_in_days","rounded_experience_in_days","experience_in_hours","rounded_experience_in_hours","code_smells","rounded_code_smells","sonar_smells","rounded_sonar_smells"]
        columns = ["lines_edited","commits","experience_in_days","experience_in_hours", "code_smells"]
        
        i = 0
        for column in columns:
            print(i," - ", column, '\n')
            i += 1
        
        if choose == 8:
            namecsv = datetime.now()
            with open(f'todos_{namecsv}.csv', 'w') as csvfile:
                print("\nmetodo,coeficiente,p_value,coluna_x,coluna_y")
                csv.writer(csvfile, delimiter=',').writerow(["metodo","coeficiente","p_value","coluna_x","coluna_y"])
                for x in range(len(columns_all)):
                    for y in range(len(columns)):
                            coef, p_value = graph.mannwhitneyu(columns_all[x], columns[y], False)
                            print(f"Mann Whitney,{coef},{p_value},{columns_all[x]},{columns[y]}")
                            csv.writer(csvfile, delimiter=',').writerow(["Mann Whitney",coef,p_value,columns_all[x],columns[y]])
                            coef, p_value = graph.pearson(columns_all[x], columns[y], False)
                            print(f"Pearson,{coef},{p_value},{columns_all[x]},{columns[y]}")
                            csv.writer(csvfile, delimiter=',').writerow(["Pearson",coef,p_value,columns_all[x],columns[y]])
                            coef, p_value = graph.spearman(columns_all[x], columns[y], False)
                            print(f"Spearman,{coef},{p_value},{columns_all[x]},{columns[y]}")
                            csv.writer(csvfile, delimiter=',').writerow(["Spearman",coef,p_value,columns_all[x],columns[y]])
                            
                    
        elif choose < 0:
            print("\n\nPor favor, escolha uma opção válida.")
        else:

            if choose < 3:
                column = str(input("\n >> Digite a coluna que deseja aplicar o método (número ou nome): "))
                
                if(column.isdigit() and int(column) < len(columns)):
                    if choose == 1:
                        graph.shapiro_text(columns[int(column)])
                    elif choose == 2:
                        graph.shapiro_plot(columns[int(column)])
                    elif choose == 0:
                        graph.new_shapiro(columns[int(column)])
                        
                elif column not in columns:
                    print("\n Essa coluna não exite!")
                elif choose == 1:
                    graph.shapiro_text(column)
                elif choose == 2:
                    graph.shapiro_plot(column)
                elif choose == 0:
                    graph.new_shapiro(column)

            elif choose > 2:
                x = str(input("\n>> Digite a coluna que será o X: "))
                y = str(input(">> Digite a coluna que será o Y: "))
                
                if(x.isdigit() and y.isdigit() and int(x) < len(columns) and int(y) < len(columns)):
                    if choose == 3:
                        graph.mannwhitneyu(columns[int(x)], columns[int(y)])
                    elif choose == 4:
                        graph.mannwhitneyu_histogram(columns[int(x)], columns[int(y)])
                    elif choose == 5:
                        graph.pearson(columns[int(x)], columns[int(y)])
                    elif choose == 6:
                        graph.spearman(columns[int(x)], columns[int(y)])
                    elif choose == 7:
                        graph.scatter(columns[int(x)], columns[int(y)])
                    elif choose == 9:
                        graph.new_mann(columns[int(x)], columns[int(y)])
                        
                elif(x not in columns or y not in columns):
                    print("\n Coluna inexistente!")
                elif choose == 3:
                    graph.mannwhitneyu(x, y)
                elif choose == 4:
                    graph.mannwhitneyu_histogram(x, y)
                elif choose == 5:
                    graph.pearson(x, y)
                elif choose == 6:
                    graph.spearman(x, y)
                elif choose == 7:
                    graph.scatter(x, y)
                elif choose == 9:
                    graph.new_mann(x, y)
        
        ex = str(input(" - Deseja realizar outra operação? (S/n):"))
        if(ex == 'n' or ex == 'N'):
            exit()