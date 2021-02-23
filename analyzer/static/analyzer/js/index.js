let alert_box = document.createElement("div")

alert_box.className = "alert alert-danger"
alert_box.setAttribute("role", "alert")

alert_box.style.position = "absolute"
alert_box.style.width = "80%"
alert_box.style.textAlign = "center"
alert_box.style.opacity = "99%"
alert_box.style.top = "30%"
alert_box.style.left = "50%"
alert_box.style.transform = "translateX(-50%)"


document.getElementById("id_1year").onclick = function () {
    let d = new Date()
    d.setMinutes(d.getMinutes() - d.getTimezoneOffset());
    d.setFullYear(d.getFullYear() - 1);
    d = d.toISOString().slice(0, 10)

    document.getElementById("id_start_date").value = d
}

document.getElementById("id_1month").onclick = function () {
    let d = new Date()
    d.setMinutes(d.getMinutes() - d.getTimezoneOffset());
    d.setMonth(d.getMonth() - 1);
    d = d.toISOString().slice(0, 10)

    document.getElementById("id_start_date").value = d
}

document.getElementById("id_6month").onclick = function () {
    let d = new Date()
    d.setMinutes(d.getMinutes() - d.getTimezoneOffset());
    d.setMonth(d.getMonth() - 6);
    d = d.toISOString().slice(0, 10)

    document.getElementById("id_start_date").value = d
}

document.getElementById("id_5day").onclick = function () {
    let d = new Date()
    d.setMinutes(d.getMinutes() - d.getTimezoneOffset());
    d.setDate(d.getDate() - 5);
    d = d.toISOString().slice(0, 10)

    document.getElementById("id_start_date").value = d
}

document.getElementById("id_ytd").onclick = function () {
    let d = new Date()
    d.setMinutes(d.getMinutes() - d.getTimezoneOffset());
    d.setMonth(0);  // january is 0
    d.setDate(1);
    d = d.toISOString().slice(0, 10)

    document.getElementById("id_start_date").value = d
}

document.querySelector("#csv-upload").ondragover = function () {
    this.className = "dropzone dragover"
    return false
}

document.querySelector("#csv-upload").onclick = function () {
    document.querySelector(".dropzone input[type='file']").click()
}

document.querySelector("#csv-upload").ondragleave = function () {
    this.className = "dropzone"
    return false
}

document.querySelectorAll("button[data-toggle='expand-table']").forEach(btn => {
    btn.onclick = function () {
        document.querySelector(btn.dataset.target).style.maxHeight = "initial"
        document.querySelector(btn.dataset.target + " .fader").remove()
        document.querySelector(btn.dataset.target + " .btn-expand").remove()
    }
})
