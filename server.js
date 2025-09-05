const http = require("http")
const cors = require("cors")
const express = require("express")

const puppeteer = require("puppeteer")

const { WebSocketServer } = require("ws")

const app = express()
const server = http.createServer(app)
const io = new WebSocketServer({ noServer: true })

app.get("/", (request, response) => {
    response.sendFile(__dirname + "/index.html")
})

io.on("connection", (socket, request) => {
    socket.on("message", (data) => {
        packet = JSON.parse(atob(data.toString()))
        console.log(packet)
        if (Object.keys(packet).length < 1) {
            socket.send(btoa(JSON.stringify({})))
        }
    })
})

server.on("upgrade", (request, socket, head) => {
    io.handleUpgrade(request, socket, head, (socket, request) => {
        io.emit("connection", socket, request)
    })
})

server.listen(0, "localhost", async () => {
    browser = await puppeteer.launch({
        headless: false,
        args: [
            // "--start-fullscreen",
            "--disable-infobars",
            "--autoplay-policy=no-user-gesture-required"
        ]
    })
    page = await browser.newPage()
    context = browser.defaultBrowserContext()
    page.setViewport({ width: Math.round(500 * (320/240)), height: 500 })
    await page.goto(`http://localhost:${server.address().port}`, { waitUntil: "networkidle2" })
})