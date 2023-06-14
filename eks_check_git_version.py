#Para que esse script funcione corretamente é necessário configurar o cli com SSO
#As relações de confiança no IAM devem estar ajustadas para permitir assumir a role através do acesso programático
#Caso tenha dúvida sobre os itens acima segue algumas documentações de referência
#https://www.learnaws.org/2022/09/30/aws-boto3-assume-role/
#https://boto3.amazonaws.com/v1/documentation/api/latest/guide/credentials.html
#https://docs.aws.amazon.com/cli/latest/userguide/sso-configure-profile-token.html#sso-configure-profile-token-auto-sso
# Nesse script foi utilizada uma lista externa no farmato .txt seguindo o modelo "[account_ID],[alias]" Ex:
# 123456989101,conta-1
# 123456989102,conta-2
# 123456989103,conta-3

import boto3
import csv
import json
import datetime

data = datetime.datetime.now()
data_formatada = data.strftime("%d%m%Y")
hora_formatada = data.strftime("%H%M%S")
output_name = data_formatada+"_"+hora_formatada

# Lista de contas extraindo de um txt
def gera_lista():
    with open('contas.txt', 'r') as arquivo:
        # Ler todas as linhas do arquivo
        linhas = arquivo.readlines()

        # Processar as linhas e criar a lista
        lista = []
        for linha in linhas:
            # Remover quebras de linha e espaços em branco
            linha = linha.strip()

            # Adicionar a linha à lista
            lista.append(linha)

    return lista

# Vetor de Regiões AWS
regions = [
    'us-east-1',
    'us-east-2',
    'us-west-1',
    'us-west-2',
    'ca-central-1',
    'sa-east-1',
    'eu-west-1',
    'eu-west-2',
    'eu-west-3',
    'eu-north-1',
    'eu-central-1',
    'ap-southeast-1',
    'ap-southeast-2',
    'ap-northeast-1',
    'ap-northeast-2',
    'ap-south-1',
    'me-south-1',
    'af-south-1',
    'eu-south-1'
]

# Assume role recebendo a conta por parametro
def assume_role(conta):

    #pega perfil configurado no AWS_CLI, nesse caso perfil via SSO
    session = boto3.Session(profile_name="[aws_profile]") # <<<<<<<<<<<<<<<<<<<<<<<<<<<< Ajustar
    sts = session.client("sts")
    response = sts.assume_role(
        #Recebe como parametro a conta contida na lista gerada
        RoleArn="arn:aws:iam::" + conta + ":role/[role_name]", # <<<<<<<<<<<<<<<<<<<<<<<<<<<< Ajustar para a nomenclatura utilizada nas role
        #Nome da sessão utilizar e-mail ou parametro autorizado na trust_reletionship da role
        RoleSessionName="[role_name]") # <<<<<<<<<<<<<<<<<<<<<< Ajustar Caso não saiba vale conferir/adicionar a condição sts:RoleSessionName no Trust relationships da role
    #criação da sessão temporária
    new_session = boto3.Session(aws_access_key_id=response['Credentials']['AccessKeyId'],
                                 aws_secret_access_key=response['Credentials']['SecretAccessKey'],
                                 aws_session_token=response['Credentials']['SessionToken'])

    return new_session

# Checa as contas que tem EKS, recebendo os parametros de conta, regiao e tipo de saida
def check_eks(contas,regions,opt):
    # Laço para percorrer as regiões por contas
    for conta in contas:
        for region in regions:
            # Exibe qual conta e qual região está sendo verificado
            contaLen = len(conta)
            print("=============================== [" + conta[0:12] + "] ==== [" + conta[13:contaLen] + "] ===== [" + region + "] ==============================")
            try:
                #ussume a role chamando a função assume_role passando a conta filtrando os 12 digitos de cada linha do arquivo
                sessao = assume_role(conta[0:12])
                # Abre a sessão que realiza a busca passando a região destino
                eks = sessao.client('eks', region_name=region)
                # Executa as verificação da existência de cluster EKS
                response = eks.list_clusters()
                # Armazena o retorno
                clusters = response['clusters']
                # alida o retorno
                if len(clusters) > 0:
                    print(f"Foram encontrados clusters EKS na região {region}:")
                    for cluster in clusters:
                        print(f"Nome do cluster: {cluster}")
                        # Chama a função e insere a linha no arquivo
                        gera_csv(opt,conta[0:12],conta[13:contaLen],region,cluster,"none")
                        
                else:
                    print(f"Não foram encontrados clusters EKS na região {region}.")
                    cluster = "Não foram encontrados clusters EKS"
                    gera_csv(opt,conta[0:12],conta[13:contaLen],region,cluster,"none")
            # Pula os erros e tbm salva no arquivo
            except Exception as e:
                print(f"*** Ocorreu um erro ao verificar os clusters EKS na região. Para mais detalhes, descomente a linha 100. ***")
                print(str(e))
                cluster = "Erro ao consultar cluster"
                gera_csv(opt,conta[0:12],conta[13:contaLen],region,cluster,e)
                continue

# Função para gerar csv recebendo como parametro o formato e o dados da consulta
def gera_csv(output_format,conta,alias,region,clusters,error):
    
    # Checa qual tipo do log e escreve no arquivo selecionado recebendo os valores da função check_eks
    if output_format == 'csv' or output_format == '1':
        with open('eks_check_'+output_name+'.csv', 'a', newline='') as file:
            writer = csv.writer(file)
            writer.writerow([conta, alias, region, clusters,error])
    elif output_format == 'json' or output_format == '2':
        with open('eks_check_'+output_name+'.json', 'a') as file:
            data = {'conta': conta, 'alias':alias, 'regiao': region, 'cluster': clusters, 'error':error}
            json.dump(data, file)
            file.write('\n')
    else:
                print("Formato de output inválido. Use 'csv' ou 'json'.")

# Gera a lista de contas extraindo de um TXT.
contas = gera_lista()

# Solicita ao usuário formato de saída desejado
while True:
    output_format = input("Escolha o formato de output (1 - CSV, 2 - JSON ou crtl+c - Sair): ").lower()
    
    if output_format == "1" or output_format == "csv":
        print("Formato escolhido: CSV")
        # Chama a função de verificação de EKS passando os parametros das demais funções
        result = check_eks(contas,regions,output_format)
        break
    elif output_format == "2" or output_format == "json":
        print("Formato escolhido: JSON")
        result = check_eks(contas,regions,output_format)
        break
    else:
        print("Opção inválida. Por favor, escolha 1 para CSV ou 2 para JSON.")


1