# F1 Web Scraping Project

Este projeto realiza web scraping de informações da Fórmula 1 e armazena os dados em um banco de dados SQLite.

## Funcionalidades

- Coleta de dados de pilotos, equipes e resultados de corridas
- Armazenamento em banco de dados SQLite
- Interface modular e extensível
- Agendamento automático de coletas
- Logs detalhados das operações

## Instalação

1. Clone o repositório
2. Instale as dependências:
```bash
pip install -r requirements.txt
```

3. Configure as variáveis de ambiente no arquivo `.env`

## Uso

### Execução básica
```bash
python main.py
```

### Coleta específica
```bash
python -m src.scrapers.drivers_scraper  # Apenas pilotos
python -m src.scrapers.races_scraper    # Apenas corridas
```

## Estrutura do Projeto

```
f1-scrapping/
├── src/
│   ├── scrapers/        # Módulos de scraping
│   ├── database/        # Gerenciamento do banco de dados
│   ├── models/          # Modelos de dados
│   └── utils/           # Utilitários
├── data/                # Banco de dados
├── logs/                # Arquivos de log
├── main.py              # Script principal
└── requirements.txt     # Dependências
```

## Fontes de Dados

- [Formula1.com](https://www.formula1.com) - Dados oficiais
- [Wikipedia F1](https://en.wikipedia.org/wiki/Formula_One) - Dados históricos

## Contribuição

1. Fork o projeto
2. Crie uma branch para sua feature
3. Commit suas mudanças
4. Push para a branch
5. Abra um Pull Request
