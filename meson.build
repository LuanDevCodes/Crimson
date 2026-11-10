# Projeto Crimson - Receita de instalação (Meson)
# O Meson é a ferramenta que sabe COPIAR cada arquivo do projeto para o lugar certo do sistema:
# o código Python, o comando 'crimson', o atalho do menu (.desktop), os metadados da loja (metainfo) e os ícones.
# Quem empacota o Crimson (ex: Flathub) só precisa chamar o Meson, sem listar comando por comando.
#
# Uso (a partir da raiz do projeto):
#   meson setup build --prefix=/usr    # prepara a pasta 'build'
#   meson test -C build                # valida o .desktop e o metainfo
#   meson install -C build            # instala tudo

project(
  'crimson',
  version: '4.0.0',
  license: 'GPL-3.0-or-later',
  meson_version: '>= 0.64.0',
)

# Encontra o Python do sistema ('pure: true' = o pacote não tem código compilado, serve para qualquer arquitetura)
python = import('python').find_installation('python3', pure: true)

# 1) Instala o pacote Python 'crimson' (código + pasta Icons) no local de bibliotecas do Python
install_subdir(
  'crimson',
  install_dir: python.get_install_dir(),
  exclude_directories: ['__pycache__'],
)

# 2) Gera e instala o comando 'crimson' a partir do modelo bin/crimson.in
conf = configuration_data()
conf.set('PYTHON', python.full_path())
configure_file(
  input: 'bin/crimson.in',
  output: 'crimson',
  configuration: conf,
  install: true,
  install_dir: get_option('bindir'),
  install_mode: 'rwxr-xr-x',
)

# 3) Atalho do menu, metadados da loja e ícones (ficam na pasta data/)
subdir('data')