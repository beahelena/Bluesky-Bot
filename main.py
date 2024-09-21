import os
from dotenv import load_dotenv
import requests
from bs4 import BeautifulSoup
import json
import time
from atproto import Client, models
import re

# Carregar variáveis de ambiente do arquivo.env
load_dotenv()

# Configurações
bluesky_handle = os.getenv('BLUESKY_HANDLE')
bluesky_password = os.getenv('BLUESKY_PASSWORD')

# Inicializa o cliente do Bluesky
client = Client()

# URL da página principal com a lista de capítulos
main_url = "https://read-given.online/"

# Fazer uma requisição para obter o conteúdo da página
response = requests.get(main_url)
def chapter_key(url):
    # Encontrar todos os números na URL
    parts = re.findall(r'(\d+)(?:-(\d+))?', url)  # Captura o número e, se existir, o sufixo
    main_chapter = int(parts[0][0])  # O primeiro número é o capítulo principal
    additional_chapter = int(parts[0][1]) if parts[0][1] else 0  # Sufixo (se existir)
    
    return (main_chapter, additional_chapter)

def get_chapter_images(chapter_url):        
        # Acessar a página de cada capítulo
        chapter_response = requests.get(chapter_url)
        
        if chapter_response.status_code == 200:
            chapter_soup = BeautifulSoup(chapter_response.content, 'html.parser')
                       
            # Encontrar todas as imagens na página do capítulo
            images = chapter_soup.find_all('img')
                                           
            images = [a['src'] for a in images if 'Given, Chapter' in a['alt']]
            
            return images
        else:
            print(f"Falha ao acessar o capítulo: {chapter_url}")


# Posta no Bluesky
def post_to_bluesky(image_path=None):
    print(f"Postando no Bluesky...")
    
    try:
        with open(image_path, 'rb') as img_file:
            img_data = img_file.read()
            upload = client.upload_blob(img_data)
            images = [models.AppBskyEmbedImages.Image(alt='',image=upload.blob)]
            embed = models.AppBskyEmbedImages.Main(images=images)


            # Adicionar um campo de texto à postagem
            post = models.AppBskyFeedPost.Record(
                text="",  # Adicionando texto à postagem
                embed=embed,
                created_at=client.get_current_time_iso()
            )


            client.com.atproto.repo.create_record(
                models.ComAtprotoRepoCreateRecord.Data(
                    repo=client.me.did,
                    collection=models.ids.AppBskyFeedPost,
                    record=post
                )
            )
            print("Imagem postada com sucesso.")

    except Exception as e:
        print(f"Erro ao postar no Bluesky: {e}")



# Verificar se a requisição foi bem-sucedida
if response.status_code == 200:
    print("Página principal acessada com sucesso.")
    soup = BeautifulSoup(response.content, 'html.parser')

    # Encontrar todos os links para os capítulos na página principal
    # Suponha que cada capítulo tenha um link com uma classe específica, como 'chapter-link'
    chapter_links = soup.find_all('a', href=True)

    # Filtrar apenas os links que contém 'chapter' na URL, para pegar os capítulos
    chapter_links = [a['href'] for a in chapter_links if 'chapter' in a['href']]
    # Remove URLs duplicadas
    chapter_links = list(dict.fromkeys(chapter_links))
    print()
    print()
    # Ordenar as URLs usando a nova função chapter_key
    urls_sorted = sorted(chapter_links, key=chapter_key)
    print(f"Encontrados {len(chapter_links)} links de capítulos.")


# Inicializa o bot
if __name__ == "__main__":
    client.login(bluesky_handle, bluesky_password)
    print("Login no Bluesky realizado com sucesso.")
    while True:
        for url in urls_sorted:
            chapter_url = url
            print(f"Acessando o capítulo: {chapter_url}")
            pagina_atual = 1
            
            images_in_chapter = get_chapter_images(chapter_url)
            qtd_paginas = len(images_in_chapter)

            for i, img in enumerate(images_in_chapter):
                    img_url = img
                    print(f"URL da imagem: {img_url}")
                    
                    print(f"Baixando imagem {i+1} de {qtd_paginas}")
                    img_response = requests.get(img_url)

                    # salvar imagem
                    img_name = f"Given_imagem_atual.jpg"
                    with open(img_name, 'wb') as img_file:
                        img_file.write(img_response.content)
                    time.sleep(1)
                    print(f"Imagem {i+1} de {qtd_paginas} baixada com sucesso.")
                    
                    # Enviar imagem para o Bluesky
                    try:
                        post_to_bluesky(img_name)
                        print('Imagem postada com sucesso.')
                    except Exception as e:
                        print(f"Erro ao postar a imagem no Bluesky: {e}")
                
                    time.sleep(3600) #espera 1 hora