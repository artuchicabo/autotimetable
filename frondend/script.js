const button = document.getElementById("sendBtn");
const responseEl = document.getElementById("response");

button.addEventListener("click", () => {
    const name = document.getElementById("nameInput").value;

    fetch("http://127.0.0.1:5000/generate", {
        method: "POST",
        headers: {
            "Content-Type": "application/json"
        },
        body: JSON.stringify({ name })
    })
    .then(res => res.json())
    .then(data => {
        responseEl.textContent = data.message;
    })
    .catch(err => {
        console.error(err);
        responseEl.textContent = "Error connecting to backend";
    });
});
