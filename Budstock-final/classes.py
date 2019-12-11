import sqlite3
from datetime import datetime
from fpdf import FPDF, HTMLMixin
from collections import OrderedDict

class MyFPDF(FPDF, HTMLMixin):
    #Necessário para a conversao de html para pdf
    pass

conn = sqlite3.connect('teste.db', check_same_thread=False)
conn.execute("PRAGMA foreign_keys = 1")
c = conn.cursor()

#Cria a tabela com os estoques
#Tabela principal
c.execute("""CREATE TABLE IF NOT EXISTS Estoques(
    codEstoque INTEGER PRIMARY KEY NOT NULL,
    nome TEXT NOT NULL
)""")

conn.commit()

#Cria a tabela para as Sessões (Relação 1 para N)
#As linhas guardam os dados referentes a sessão de cada estoque
#Cada estoque pode ter somente 1 sessão ativa
#As sessões são mantidas até esta ser encerrada pelo usuário
#Ao deletar o estoque, a sessão ativa é deletada da tabela de Sessões
c.execute("""CREATE TABLE IF NOT EXISTS Sessoes(
            receita REAL NOT NULL,
            hora_ini TEXT NOT NULL,
            hora_fim TEXT NOT NULL,
            estoque INTEGER NOT NULL,
            FOREIGN KEY (estoque) REFERENCES Estoques(codEstoque) ON DELETE CASCADE
            )""")

conn.commit()

#Cria a tabela para os arquivos html dos relatorios (Relação 1 para N)
#Uma tabela para todos os relatórios
#Funciona de forma similar a tabela de Sessões
c.execute("""CREATE TABLE IF NOT EXISTS Relatorios(
            hora_ini TEXT NOT NULL,
            rel_html BLOB NOT NULL,
            rel_html_css BLOB NOT NULL,
            estoque INTEGER NOT NULL,
            FOREIGN KEY (estoque) REFERENCES Estoques(codEstoque) ON DELETE CASCADE
            )""")

conn.commit()




class Estoque:
    # 1 ATRIBUTO ; 1 METODOS

    def __init__(self, estoque):
        # estoque = nome do estoque;
        self.estoque = estoque

    def criar_tabela(self):
        # Insere o estoque no banco de dados e cria uma tabela correspondente
        # Não é possível inserir o estoque se o nome já estiver ocupado
        c.execute("SELECT * FROM Estoques WHERE nome=?", (self.estoque,))
        check = c.fetchone()
        if not check and self.estoque:
            with conn:
                c.execute("INSERT INTO Estoques (nome) VALUES (?)", (self.estoque,))
            with conn:
                c.execute("""CREATE TABLE IF NOT EXISTS [""" + self.estoque + """](
            numero INTEGER NOT NULL,
            nome TEXT NOT NULL,
            preço REAL NOT NULL,
            quantidade INTEGER NOT NULL,
            estoque INTEGER NOT NULL,
            FOREIGN KEY (estoque) REFERENCES Estoques(codEstoque) ON DELETE CASCADE
            )""")

    @staticmethod
    def remover_estoque(nome_estoque):
        # Recebe o nome do estoque
        # Remove o estoque do Banco e os produtos contidos nesse estoque
        with conn:
            c.execute("DELETE FROM Estoques WHERE nome=?", (nome_estoque,))
        with conn:
            c.execute("DROP TABLE IF EXISTS ["+nome_estoque+"]")

    @staticmethod
    def alterar_estoque(estoque_antigo, estoque_novo):
        # Altera o nome do estoque
        c.execute("SELECT * FROM Estoques WHERE nome=?", (estoque_novo,))
        check = c.fetchone()
        if not check and estoque_novo:
            c.execute("UPDATE Estoques SET nome=?  WHERE nome=?",(estoque_novo, estoque_antigo))
            c.execute("ALTER TABLE [" + estoque_antigo + "] RENAME TO [" + estoque_novo + "]")
            conn.commit()
            return True
        return False
        

    def mostrar_estoque(self):
        # Retorna uma lista dos produtos dentro do estoque
        print (self.estoque)
        with conn:
            c.execute("SELECT numero,nome,preço,quantidade FROM ["+self.estoque+ "] ORDER BY numero")

        return (c.fetchall())

    @staticmethod
    def gerar_li_li_tup(estoque):
        # Função para criar os nomes ( começando por 0) das informações para o request_form
        prod = str(estoque.mostrar_estoque()).translate({ord(c): '' for c in "[]()'"})
        prod = list(prod.split(","))

        li_li_tup = []
        y = []
        s = ["numero", "nome", "preço", "quantidade"]
        z = 0
        k = 0
        for info in prod:
            j = str(k)
            tup = (s[z] + j, info)
            y.append(tup)
            if z == 3:
                k = k + 1
                li_li_tup.append(y)
                y = []
            z = (z + 1) % 4
        return li_li_tup

    @staticmethod
    def mostrar_estoques():
        # Para testes: printa os estoques no banco
        c.execute("SELECT * FROM Estoques")
        return c.fetchall()

    @staticmethod
    def get_estoque_nome(estoque_num):
        # Para testes: printa os estoques no banco
        c.execute("SELECT nome FROM Estoques WHERE codEstoque=?",(estoque_num,))
        lista = c.fetchone()
        return lista[0]

    @staticmethod
    def cod_estoque(nome):
        # retorna a chave do estoque
        c.execute("SELECT * FROM Estoques WHERE nome = ?", ( nome,))
        lista = c.fetchone()
        return lista[0]

class Produto:
    # 5 ATRIBUTOS; 3 METODOS

    def __init__(self, numero, nome, preço, quantidade, estoque_nome):

        # O ultimo atributo recebe o nome do estoque ao qual o produto pertence
        self.numero = numero
        self.nome = nome
        self.preço = preço
        self.quantidade = quantidade
        self.estoque_nome = estoque_nome

    def produto_novo(self):

        # Insere o produto na tabela correspondente ao seu estoque
        # Caso o Numero OU o Nome já estejam ocupados, o metodo não insere o produto
        if self.numero  or self.nome or self.preço or self.quantidade:
            erro = 1
            if self.numero  and self.nome and self.preço and self.quantidade:
                try:
                    int(self.numero)
                    float(self.preço)
                    int(self.quantidade)
                    c.execute("SELECT * FROM [" + self.estoque_nome + "] WHERE nome=? OR numero=? ", (self.nome, self.numero))
                    check = c.fetchone()
                    if not check:
                        if int(self.quantidade) >= 0 and int(self.numero) >= 0 and float(self.preço) >= 0:
                            c.execute("SELECT * FROM Estoques WHERE nome = ?", (self.estoque_nome,))
                            lista = c.fetchone()
                            c.execute("INSERT INTO [" + self.estoque_nome + "] VALUES (?, ?, ?, ?, ?)", (self.numero, self.nome,self.preço, self.quantidade,lista[0]))
                            conn.commit()
                            erro = 0
                except TypeError:
                    pass
                except ValueError:
                    pass
            return erro
        else : 
            return 2

    def alterar_produto(self, nro_prod):

        # Atualiza todas as informações do produto com o Numero equivalente a "nro_prod"
        # Metodo criado a fim do objeto utilizado possuir 1 ou mais atributos a serem atualizados
        # Caso o Numero OU o Nome já estejam ocupados, o metodo não atualiza o produto
        # c.execute("SELECT * FROM "+self.estoque_nome+" WHERE nome=? OR numero=? ",(self.nome,self.numero))
        erro = True
        if self.numero  and self.nome and self.preço and self.quantidade:
            try:
                int(self.numero)
                float(self.preço)
                int(self.quantidade)
                c.execute("SELECT * FROM [" + self.estoque_nome + "] WHERE numero=? ", (self.numero,))
                check = c.fetchone()
                if not check or int(self.numero) == int(nro_prod):
                    c.execute("SELECT * FROM [" + self.estoque_nome + "] WHERE nome=? ", (self.nome,))
                    check = c.fetchone()
                    if not check or check[0] == nro_prod:
                        if int(self.quantidade) >= 0 and int(self.numero) >= 0:
                            c.execute(
                                "UPDATE [" + self.estoque_nome + "] SET numero=?, nome=?, preço=?, quantidade=?  WHERE numero=?",
                                (self.numero, self.nome, self.preço, self.quantidade, nro_prod))
                            conn.commit()
                            erro = False
                            print(erro)
            except TypeError:
                pass
            except ValueError:
                pass
        print(erro)
        return erro

    def remover_produto(self):

        # Remove o produto de sua tabela/estoque correspondente
        with conn:
            c.execute("DELETE FROM [" + self.estoque_nome + "] WHERE numero=?", (self.numero,))

class Sessao:

    def __init__(self, estoque_nome, hora_ini, receita = 0, hora_fim = "0/0/0", ):
        self.receita = receita
        self.hora_ini = hora_ini
        self.hora_fim = hora_fim
        self.estoque_nome = estoque_nome

    def sessao_nova (self):
        # Insere a sessão na tabela de sessões e cria uma tabela para os produtos vendidos
        # Se a sessão nao foi encerrada, os dados antigos permanecerão
        cod = Estoque.cod_estoque(self.estoque_nome)
        c.execute("SELECT * FROM Sessoes WHERE estoque=? ", (cod,))
        check = c.fetchone()
        if not check:
            with conn:
                c.execute("INSERT INTO Sessoes VALUES (?, ?, ?, ?)", ( self.receita, self.hora_ini, 
                                                                  self.hora_fim, cod))
        with conn:
            c.execute("""CREATE TABLE IF NOT EXISTS [""" + self.estoque_nome + """_vendidos](
                numero INTEGER NOT NULL,
                nome TEXT NOT NULL,
                preço REAL NOT NULL,
                quantidade INTEGER NOT NULL
                )""")

    @staticmethod
    def adicionar_receita (estoque, valor):
        #Adiciona o valor do subtotal de um carrinho confirmado
        cod = Estoque.cod_estoque(estoque)
        c.execute("SELECT receita FROM Sessoes WHERE estoque=? ", ( cod,))
        check = c.fetchone()
        x = check[0]
        x = x + valor
        c.execute("UPDATE Sessoes SET receita=? WHERE estoque=?",( x, cod))
        conn.commit()
    
    @staticmethod
    def adicionar_hora_fim (estoque, hora):
        #Insere a hora em que a sessão é encerrada
        c.execute("UPDATE Sessoes SET hora_fim=? WHERE estoque=?",( hora, Estoque.cod_estoque(estoque)))
        conn.commit()

    @staticmethod
    def get_vendidos (estoque):
        #Coleta todos os produtos vendidos durante a sessão 
        c.execute("SELECT * FROM [" + estoque + "_vendidos] ORDER BY numero ")
        check = c.fetchall()
        return check

    @staticmethod
    def get_sessao (estoque):
        #Coleta os dados referentes a sessão
        c.execute("SELECT receita,hora_ini,hora_fim FROM Sessoes WHERE estoque=? ",(Estoque.cod_estoque(estoque),))
        check = c.fetchall()
        return check[0]


    @staticmethod
    def fechar_sessao (estoque):
        #Deleta a linha  correspondente a sessão da tabela Sessões e deleta a tabela utilizada para manter
        #os produtos vendidos na sessão.
        #Dessa forma, quando o aplicativo é fechado durante uma sessão, os dados da sessão não são perdidos.
        with conn:
            c.execute("DELETE FROM Sessoes WHERE estoque=?", (Estoque.cod_estoque(estoque),))
        with conn:
            c.execute("DROP TABLE  ["+ estoque +"_vendidos]")

class Prod_Vendido:

    def __init__(self, numero, nome, quantidade, preço, estoque_nome):
            self.numero = numero
            self.nome = nome
            self.quantidade = quantidade
            self.preço = preço
            self.estoque_nome = estoque_nome

    
    def vendido(self):
        #Inseri os produtos do carrinho à tabela de produtos vendidos,
        # conferindo se o produto já existe ou não nessa tabela
        # Retira do estoque a quantidade vendida do produto 
        c.execute("SELECT numero FROM [" + self.estoque_nome + "_vendidos] WHERE numero=? ",
                                                             (self.numero,))
        check = c.fetchone()
        if check:
            c.execute("SELECT quantidade FROM [" + self.estoque_nome + "_vendidos] WHERE numero=? ", 
                                                                    (self.numero,))
            check = c.fetchone()
            x = check[0]
            x = x + int(self.quantidade)
            c.execute("UPDATE [" + self.estoque_nome + "_vendidos] SET quantidade=?  WHERE numero=?",
                                                                    ( x, self.numero))
            conn.commit()
        else:
            c.execute("INSERT INTO [" + self.estoque_nome + "_vendidos] VALUES (?, ?, ?, ?)", (self.numero, self.nome,
                                                                                           self.preço, self.quantidade))
            conn.commit()
        c.execute("SELECT quantidade FROM [" + self.estoque_nome + "] WHERE numero=? ",
                                                             (self.numero,))
        check = c.fetchone()
        x = check[0]
        x = x - int(self.quantidade)
        c.execute("UPDATE [" + self.estoque_nome + "] SET quantidade=?  WHERE numero=?",
                                                                    ( x, self.numero))
        conn.commit()

class Relatorio:

    @staticmethod
    def guardar (estoque, hora_ini, html, html_css):
        #Guarda o arquivo html no banco
        cod = Estoque.cod_estoque(estoque)
        c.execute("INSERT INTO Relatorios VALUES (?, ?, ?, ?)", (hora_ini, html, html_css, cod))
        conn.commit()

    @staticmethod
    def get_list (estoque):
        #Coleta a lista de relatorios guardados para o estoque correspondente
        cod = Estoque.cod_estoque(estoque)
        c.execute("SELECT hora_ini FROM Relatorios WHERE estoque = ? ORDER BY hora_ini DESC", ( cod,))
        return (c.fetchall())

    @staticmethod
    def get_rel_css (estoque, hora_ini):
        #Retorna o arquivo html do relatorio com a hora de inicio de sessao correspondente
        cod = Estoque.cod_estoque(estoque)
        c.execute("SELECT rel_html_css FROM Relatorios WHERE estoque = ? AND hora_ini = ?", ( cod, hora_ini))
        lista = c.fetchone()
        return lista[0]

    @staticmethod
    def get_rel (estoque, hora_ini):
        #Retorna o arquivo html do relatorio com a hora de inicio de sessao correspondente
        cod = Estoque.cod_estoque(estoque)
        c.execute("SELECT rel_html FROM Relatorios WHERE estoque = ? AND hora_ini = ?", ( cod, hora_ini))
        lista = c.fetchone()
        return lista[0]

    @staticmethod
    def del_rel (estoque, hora_ini):
        #Retira o relatório com a hora_ini dada da tabela de relatorios
        cod = Estoque.cod_estoque(estoque)
        c.execute("DELETE FROM Relatorios WHERE estoque=? AND hora_ini = ?", (cod, hora_ini))
        conn.commit()