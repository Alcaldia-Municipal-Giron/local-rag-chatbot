# ---------------------------------------------------------
# Construye el contexto textual que posteriormente
# será utilizado por el modelo generativo.
#
# Recibe los resultados obtenidos por el retriever
# y convierte los chunks recuperados en un único texto.
# ---------------------------------------------------------

def construir_contexto(resultados):

    fragmentos = []

    for posicion, resultado in enumerate(resultados, start=1):

        texto = resultado["text"]

        print(
            f"[CONTEXTO] Fragmento {posicion} | "
            f"Caracteres: {len(texto)}"
        )

        fragmento = (
            f"[Fragmento {posicion}]\n"
            f"{texto}"
        )

        fragmentos.append(fragmento)

    contexto = "\n\n".join(fragmentos)

    print(
        f"[CONTEXTO] Total caracteres: {len(contexto)}"
    )

    return contexto