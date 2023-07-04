$(document).ready(function () {
  const received = $("#received");
  const wsUrl = Object.assign(new URL(window.location.href), { protocol: "ws", pathname: "/ws" });
  var socket;

  const connect = function () {
    socket = new WebSocket(wsUrl);

    socket.onerror = function (err) {
      console.error("websocket error");
      socket.close();
    };

    socket.onopen = function () {
      console.info("websocket connected");
    };

    socket.onmessage = function (message) {
      console.info("websocket receiving: " + message.data);
      receiveMessage(message);
    };

    socket.onclose = function (e) {
      console.log("websocket disconnected");
      setTimeout(function () {
        connect();
      }, 1000);
    };
  };
  connect();

  const sendMessage = function (message) {
    console.log("websocket sending: " + message.data);
    socket.send(message.data);
  };

  const receiveMessage = function (message) {
    received.append(message.data);
    received.append($("<br/>"));
  };
  // GUI Stuff

  // send a command to the serial port
  $("#cmd_send").click(function (ev) {
    ev.preventDefault();
    var cmd = $("#cmd_value").val();
    sendMessage({ data: cmd });
    $("#cmd_value").val("");
  });

  $("#clear").click(function () {
    received.empty();
  });
});
