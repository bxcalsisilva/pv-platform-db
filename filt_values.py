def filt_rej_check():
    # Variables de rechazo Umbral validos / Rechazo horas / x2 / Rechazo día / Rechaza inicion / Rechazar fin
    # filt_rej_check = [IntVar(value=1), IntVar(value=1), IntVar(value=1),IntVar(value=0), IntVar(value=0), IntVar(value=0)]
    filts = [1, 1, 1, 1, 1, 1]
    return filts


def filt_rej_val(mode="hourly"):
    # for x in range(6): a = IntVar(); a.set(1); filt_rej_check.append(a)
    filts = ["2", "5", "19", "10"]
    if mode == "hourly":
        val = "10"
    elif mode == "daily":
        val = "9"
    filts.append(val)

    if mode == "hourly":
        val = "14"
    elif mode == "daily":
        val = "17"
    filts.append(val)

    filts.append("IEC-61724-3")

    if mode == "daily":
        filts.append("None")

    return filts


def filt_treat_check(mode="hourly"):
    # for x in range(7): a = StringVar(); filt_rej_val.append(a)
    # Variables de tratamiento Reemplazo, sombras, datos alternativos agrupacion
    filts = [1, 1, 0]

    if mode == "hourly":
        val = 0
    elif mode == "daily":
        val = 1
    filts.append(val)

    return filts


def filt_treat_val():
    # for x in range(2): a = IntVar(); a.set(1); filt_treat_check.append(a)
    # for x in range(2): a = IntVar(); a.set(0); filt_treat_check.append(a)
    filts = ["2", "15"]

    return filts


# for x in range(2): a = StringVar(); filt_treat_val.append(a)
# Conjunto de valores de filtros


def filt_rej_check2():
    filts = [1, 1, 1, 0, 0, 0]

    return filts


def filts_hourly(mode="hourly"):
    """Configure the filtering processing for hourly analysis."""

    filt_values = [
        filt_rej_check(),
        filt_rej_val(mode),
        filt_treat_check(mode),
        filt_treat_val(),
    ]

    return filt_values


def filts_daily(mode="daily"):

    filt_values = [
        filt_rej_check(),
        filt_rej_val(mode),
        filt_treat_check(mode),
        filt_treat_val(),
    ]

    alt_filt_values = [
        filt_rej_check2(),
        filt_rej_val(mode),
        filt_treat_check(mode),
        filt_treat_val(),
    ]

    return filt_values, alt_filt_values
