from flask import Flask, render_template, url_for, flash, redirect, request, make_response
import sqlite3
from datetime import datetime
from fpdf import FPDF, HTMLMixin
from collections import OrderedDict
from classes import MyFPDF, Estoque, Produto, Sessao, Prod_Vendido, Relatorio


app = Flask(__name__)

app.config['SECRET_KEY'] = 'U dont know my key '


@app.route("/", methods=['GET', 'POST'])
def teste():
    repeat = Estoque.mostrar_estoques()
    tam = len(repeat)
    if request.method == "POST":
        #Confere se algum estoque foi deletado e deleta
        for i in range(tam):
            repeat[i]
            for re in repeat:    
                if str(re[1]) in request.form:
                    estoque = re[1]
                    Estoque.remover_estoque(str(estoque))
                    flash('O estoque {} foi exluído.'.format(str(estoque)), 'success')
                    return redirect(url_for('teste'))
        #Confere se algum estoque foi adicionado e adiciona
    if "add" in request.form:
        for re in repeat:
            #if Estoque(request.form.get('novo_estoque')) in repeat:
            if re[1] == request.form["novo_estoque"]:
                flash('O estoque já existe ','warning')
                return redirect(url_for('teste'))
        else:
            stock = Estoque(request.form.get('novo_estoque'))
            Estoque.criar_tabela(stock)
    
    lista = []
    repeat = Estoque.mostrar_estoques()
    for re in repeat:
        lista.append(re[1])
    return render_template('home.html', len=len(lista), repeat=lista)


@app.route("/estoque", methods=['GET', 'POST'])
def pag_estoque():
    # Metodos Get e Post para manter o nome do estoque na pagina
    if request.method == "GET":
        estoque_info = request.args.get('info')
    elif request.method == "POST":
        print('é o metodo post')
        estoque_info = request.form["nome_estoque"]
        print("Nome do estoque dento de post :",estoque_info)
    estoque = Estoque(estoque_info)
    print("Nome do estoque :",estoque.estoque)
    estoque.criar_tabela()
    # Checando de o Botão " Vendas" foi pressionado
    if "vendas" in request.form:
        return redirect(url_for('pag_vendas',info=estoque.estoque))
    if "relatorios" in request.form:
        return redirect(url_for('pag_relatorios',info=estoque.estoque))
    if "n_estoque" in request.form:
        novo_estoque = request.form["novo_estoque"]
        antigo_estoque = estoque_info
        con = Estoque.alterar_estoque(antigo_estoque,novo_estoque)
        if con:
            estoque = Estoque(novo_estoque)
            li_li_tup = Estoque.gerar_li_li_tup(estoque)
            flash('O estoque foi renomeado para {}.'.format(str(novo_estoque)), 'success')
            return render_template('estoque.html', li_li_tup=li_li_tup, estoque=estoque.estoque)
        else:
            li_li_tup = Estoque.gerar_li_li_tup(estoque)
            flash('O estoque {} já existe.'.format(str(novo_estoque)),'warning')
            return render_template('estoque.html', li_li_tup=li_li_tup, estoque=estoque.estoque)

    if request.method == "POST":
        # Checando se o Botão "Atualizar Valores" foi pressionado
        if "atualizar" in request.form:
            print("Nome do estoque dentro de 'atualizar' :",estoque.estoque)
            # Função para Atualizar a tabela
            w = 0
            for prods in estoque.mostrar_estoque():
                z = str(w)
                prod = Produto(request.form["numero" + z], request.form["nome" + z], request.form["preço" + z],
                            request.form["quantidade" + z], estoque.estoque)
                erro = prod.alterar_produto(prods[0])
                if bool(erro):
                    flash('Entrada Invalida em Produto Alterado','warning')
                    return redirect(url_for('pag_estoque', info=estoque.estoque))
                w = w + 1

            # Função para Adicionar novo produto
            prodnovo = Produto(request.form["numeron"], request.form["nomen"], request.form["preçon"],
                            request.form["quantidaden"], estoque.estoque)
            erro = prodnovo.produto_novo()
            if erro == 0:
                flash('O produto foi adicionado ao estoque.')
                return redirect(url_for('pag_estoque', info=estoque.estoque))
            elif erro == 1:
                flash('Entrada Invalida em Novo Produto','warning')
                return redirect(url_for('pag_estoque', info=estoque.estoque))

        # Função para Deletar um produto do estoque
        else:
            z = 2
            for produto in estoque.mostrar_estoque():
                y = str(z)
                #Se um botao de deletar foi pressionado
                if y in request.form:
                    del_produto = Produto(produto[0], produto[1], produto[2], produto[3], estoque.estoque)
                    del_produto.remover_produto()
                    flash('O produto foi removido do estoque.')

                z = z + 1

    li_li_tup =Estoque.gerar_li_li_tup(estoque)
    return render_template('estoque.html', li_li_tup=li_li_tup, estoque=estoque.estoque)



@app.route("/vendas", methods=['GET','POST'])
def pag_vendas():
    if request.method == "GET":
        estoque_info = request.args.get('info')
        estoque = Estoque(estoque_info)

        #Insere a sessao na tabela de Sessoes e cria uma tabela Prod_vendidos para a sessão
        data_hora = datetime.now().strftime("%Y/%m/%d %H:%M:%S")
        sessao = Sessao(estoque_info, data_hora)
        sessao.sessao_nova()

        li_li_tup = Estoque.gerar_li_li_tup(estoque)
        
        return render_template('vendas.html', li_li_tup=li_li_tup, estoque=estoque.estoque)
                   

@app.route("/carrinho", methods=['POST','GET'])
def pag_carrinho():
    if "carrinho" in request.form:
        # Função para enviar os produtos selecionados para o carrinho usando dicionario
        dic = OrderedDict()
        li_dic = []
        s = ["numero", "nome", "preço", "quantidade"]
        z = 0
        w = 0
        val = 0
        preço = 0
        while "numero"+str(z) in request.form:
            if int(request.form["quantidade"+str(z)]) > 0 :
                for k in range(4):
                    dic[s[k]+str(w)] = request.form[s[k]+str(z)]
                    if k == 2:
                        preço = request.form[s[k]+str(z)]
                    if k == 3:
                        val = val + float(preço)*float(request.form[s[k]+str(z)])
                        preço = 0
                    print(dic)
                li_dic.append(dic)
                print(li_dic)
                w = w + 1
                dic = OrderedDict()
            z = z+1
        val = '{:.2f}'.format(val)
        print(li_dic)

        return render_template('carrinho.html', li_dic = li_dic, estoque = request.form["nome_estoque"], subtotal = val )
    elif "reset" in request.form:
        #Recarrega a pagina para 'resetar' as quantidades selecionadas
        estoque = Estoque(request.form["nome_estoque"])
        li_li_tup = Estoque.gerar_li_li_tup(estoque)
        return render_template('vendas.html', li_li_tup=li_li_tup, estoque=estoque.estoque)

    elif "confirmar" in request.form:
        # Função para confirmar a venda dos produtos, retirar quantidade do estoque e adicionar na tabela _vendidos
        estoque = Estoque(request.form["nome_estoque"])
        prod_v = Prod_Vendido(0,"0",0,0,estoque.estoque)
        z = 0
        val = 0
        while "numero"+str(z) in request.form:
            prod_v.numero = request.form["numero"+str(z)]
            prod_v.nome = request.form["nome"+str(z)]
            prod_v.preço = request.form["preço"+str(z)]
            prod_v.quantidade = request.form["quantidade"+str(z)]
            prod_v.vendido()
            val = val + float(prod_v.preço)*int(prod_v.quantidade)
            z = z+1
        Sessao.adicionar_receita(estoque.estoque, val)

        li_li_tup = Estoque.gerar_li_li_tup(estoque)
        flash('Produtos vendidos','success')
        return render_template('vendas.html', li_li_tup=li_li_tup, estoque=estoque.estoque)

    elif "cancel" in request.form:
        #Descarta o carrinho/Recarrega a pagina de vendas
        estoque = Estoque(request.form["nome_estoque"])
        li_li_tup = Estoque.gerar_li_li_tup(estoque)
        flash('Carrinho esvaziado','success')
        return render_template('vendas.html', li_li_tup=li_li_tup, estoque=estoque.estoque)
            
    elif "alterar" in request.form:
        print("alterar em request.form")
        estoque = Estoque(request.form["nome_estoque"])
        # Função DIFERENCIADA para criar os nomes ( começando por 0) das informações para o request_form
        # Mantem a quantidade de cada produto selecionado
        prod = str(estoque.mostrar_estoque()).translate({ord(c): '' for c in "[]()'"})
        prod = list(prod.split(","))
        print(request.form)
        print(prod)
        print(request.form["numero" + str(0)])

        li_li_tup = []
        li_tup = []
        s = ["numero", "nome", "preço", "quantidade"]
        z = 0
        k = 0
        w = 0
        u = 0
        for info in prod:
            j = str(k)
            if "numero" + str(w) in request.form:
                print("numero+str(w) em request.form; w = ", w)
                if z == 0 and int(info) == int(request.form["numero" + str(w)]):
                    u = 1
                if z == 3 and u == 1:
                    tup = (s[z] + j, request.form["quantidade" + str(w)])
                    w = w+1
                    u = 0
                elif z == 3:
                    tup = (s[z] + j, 0)
                else :
                    tup = (s[z] + j, info)
                li_tup.append(tup)
                if z == 3:
                    k = k + 1
                    li_li_tup.append(li_tup)
                    li_tup = []
                z = (z + 1) % 4
                print(li_li_tup)
        return render_template('vendas.html', li_li_tup=li_li_tup, estoque=estoque.estoque, atualizar = True)

    elif "encerrar" in request.form:
        #Vai para a pagina de sessao_fim
        return redirect(url_for('pag_sessao_fim',info=request.form["nome_estoque"]))
    
    elif "suspender" in request.form:
        #Vai para a pagina de estoque sem que a sessão seja encerrada
        return redirect(url_for('pag_estoque',info=request.form["nome_estoque"]))

@app.route("/sessao_fim", methods=['GET','POST'])
def pag_sessao_fim():
    if request.method == 'GET':
        #Finaliza a coleta de dados e apresenta o relatorio
        estoque_info = request.args.get('info')
        data_hora = datetime.now().strftime("%Y/%m/%d %H:%M:%S")
        Sessao.adicionar_hora_fim(estoque_info, data_hora)
        li_li = Sessao.get_vendidos(estoque_info)
        sess = Sessao.get_sessao(estoque_info)
        receita = "{:.2f}".format(sess[0])
        return render_template('sessao_fim.html', receita = receita, hora_ini = sess[1], hora_fim = sess[2], li_li = li_li, estoque = estoque_info, pagina = True)
    if request.method == 'POST':
        estoque_info = request.form["nome_estoque"]
        if "nao_salvar" in request.form:
                #Descarta o relatorio apresentado
                Sessao.fechar_sessao(estoque_info)
                flash('Relatório descartado','success')
                return redirect(url_for('pag_estoque',info=estoque_info))
        if "salvar" in request.form:
            #Guarda o arquivo html da pagina(com as informações apresentadas)
            li_li = Sessao.get_vendidos(estoque_info)
            sess = Sessao.get_sessao(estoque_info)
            estoque_num = Estoque.cod_estoque(estoque_info)
            receita = "{:.2f}".format(sess[0])
            rendered = render_template('relatorio.html', receita = receita, hora_ini = sess[1], hora_fim = sess[2], li_li = li_li, estoque = estoque_info, estoque_num = estoque_num)
            rendered_css = render_template('relatorio_css.html', receita = receita, hora_ini = sess[1], hora_fim = sess[2], li_li = li_li, estoque = estoque_info, estoque_num = estoque_num)
            Relatorio.guardar(estoque_info,sess[1], rendered, rendered_css)
            Sessao.fechar_sessao(estoque_info)
            flash('Arquivo salvo','success')
            return redirect(url_for('pag_estoque',info=estoque_info))
       

@app.route("/relatorios", methods=['GET', 'POST'])
def pag_relatorios():
    if request.method == 'GET':
        #Apresenta a lista de relatorios disponiveis 
        estoque = request.args.get("info")
        li = Relatorio.get_list(estoque)
        dic = OrderedDict()
        z = 0
        for hora in li:
            dic["rel"+str(z)] = hora[0]
            z = z+1
        return render_template('relatorios.html', dic = dic, estoque = estoque)
    if request.method == 'POST':
        #Deleta do banco o relatorio selecionado da lista
        estoque = request.form["nome_estoque"]
        li = Relatorio.get_list(estoque)
        for z in range(len(li)):
            if "rel"+str(z) in request.form:
                hora_ini = li[z]
                hora_ini = hora_ini[0]
                Relatorio.del_rel(estoque, hora_ini)
                flash('Relatório deletado','success')

        li = Relatorio.get_list(estoque)
        dic = OrderedDict()
        z = 0
        for hora in li:
            dic["rel"+str(z)] = hora[0]
            z = z+1
        return render_template('relatorios.html', dic = dic, estoque = estoque)


@app.route("/relatorio", methods=['GET','POST'])
def pag_relatorios_rel():
    if request.method == 'GET':
        # Apresenta o arquvivo html guardado no banco
        # Se o nome do estoque tiver sido alterado depois da sessão de vendas do relatorio apresentado,
        # o nome do estoque vigente durante a sessão ainda será apresentado no relatorio,
        # visto que o html guardado é um 'arquivo estatico' já renderizado
        estoque = request.args.get("info")
        hora_ini = request.args.get("h_ini")
        rendered = Relatorio.get_rel_css(estoque, hora_ini)
        return rendered
    if request.method == 'POST':
        if "baixar" in request.form:
            # Baixa no dispositivo o arquivo em formato PDF
            # Os botoes do arquivo html não aparecem no PDF pois a biblioteca FPDF não suporta a tag <input>
            hora_ini = request.form["hora_ini"]
            estoque = request.form["nome_estoque"]
            rendered = Relatorio.get_rel(estoque, hora_ini)
            hora_str = str(hora_ini).translate({ord(c): '' for c in " "})
            pdf = MyFPDF()
            pdf.add_page()
            pdf.write_html(rendered)
            response = make_response(pdf.output(dest='S').encode('latin-1'))
            response.headers['Content-Type'] = 'application/pdf'
            response.headers['Content-Disposition'] = 'attachment; filename='+estoque+'_'+hora_str+'.pdf'
            return response
        if "delete" in request.form:
            #Deleta o relatorio e volta para a pagina de relatorios
            hora_ini = request.form["hora_ini"]
            estoque = request.form["nome_estoque"]
            Relatorio.del_rel(estoque, hora_ini)
            flash('Relatório deletado','success')
            return redirect(url_for('pag_relatorios',info=estoque))

        if "voltar" in request.form:
            #Volta para a pagina de relatorios
            estoque_num = request.form["estoque_num"]
            estoque = Estoque.get_estoque_nome(estoque_num)
            return redirect(url_for('pag_relatorios',info=estoque))



if __name__ == '__main__':
    app.run(debug=True, use_reloader=True)