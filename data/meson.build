# Projeto Crimson - Instalação dos arquivos de integração com o desktop Linux

app_id = 'io.github.luandevcodes.Crimson'

# Atalho do menu de aplicativos (.desktop)
desktop_file = files(app_id + '.desktop')
install_data(desktop_file, install_dir: get_option('datadir') / 'applications')

# Metadados da loja (AppStream): é o que aparece na página do app no GNOME Software, KDE Discover e Flathub
metainfo_file = files(app_id + '.metainfo.xml')
install_data(metainfo_file, install_dir: get_option('datadir') / 'metainfo')

# Ícones: os mesmos arquivos de crimson/Icons, instalados com o nome oficial do app (o 'rename' evita duplicar arquivos)
install_data(
  '../crimson/Icons/Crimson.svg',
  rename: app_id + '.svg',
  install_dir: get_option('datadir') / 'icons/hicolor/scalable/apps',
)
install_data(
  '../crimson/Icons/Crimson.png',
  rename: app_id + '.png',
  install_dir: get_option('datadir') / 'icons/hicolor/512x512/apps',
)

# Testes automáticos (rodam com 'meson test -C build'): só rodam se a ferramenta existir no computador
desktop_validate = find_program('desktop-file-validate', required: false)
if desktop_validate.found()
  test('Validar arquivo .desktop', desktop_validate, args: [desktop_file])
endif

appstreamcli = find_program('appstreamcli', required: false)
if appstreamcli.found()
  test('Validar metainfo (AppStream)', appstreamcli, args: ['validate', '--no-net', '--explain', metainfo_file])
endif
