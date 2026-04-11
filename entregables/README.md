# Entregables / Deliverables

Este directorio contiene archivos de entregables del proyecto académico.

## Nota sobre archivos binarios

Los archivos `.docx`, `.zip`, `.pptx` y otros binarios grandes **no deberían versionarse en git** directamente porque:

1. No permiten diffs significativos
2. Inflan el tamaño del repositorio
3. Cada versión crea un objeto completo nuevo

## Alternativas recomendadas

### Para documentos
- Exportar a PDF para versionado final
- Usar Google Docs/Office 365 para colaboración en tiempo real
- Mantener solo la versión final en el repo

### Para datos
- Usar Git LFS si es necesario versionar
- Almacenar en cloud storage (Google Drive, OneDrive, etc.)
- Referenciar desde el README con enlaces externos

## Archivos actuales

- `Proyecto_Smart_Cities_BigData.docx` - Documento principal del proyecto
- `ArchivosUsados.zip` - Archivos de datos utilizados

Estos archivos están aquí por conveniencia del proyecto académico, pero considera moverlos a almacenamiento externo para un proyecto de producción.
