#include <WiFi.h>
#include <WebServer.h>

#define servoPin 13 // Pin al que conectas el servo
int retardo = 3000; // Retardo base, no se usa en el servo pero mantenemos la variable
int tiempo = 200;   // No se usa en el servo pero mantenemos la estructura
const char* ssid = "RedmiJC";
const char* password = "12345678";
WebServer server(80);

// Función para mover el servo
void moverServo(int angulo) {
  int pulseWidth = map(angulo, 90, 180, 1650, 2300); // Convierte el ángulo en duración del pulso
  digitalWrite(servoPin, HIGH);
  delayMicroseconds(pulseWidth);
  digitalWrite(servoPin, LOW);
  delay(20 - pulseWidth / 1000); // Control del ciclo de tiempo
}

// Función `giro` para mover el servo
void giro(int dummy1, int dummy2, int dummy3) {
  // Mueve el servo de 90 a 180 grados
  for (int pos = 90; pos <= 180; pos += 1) {
    moverServo(pos);
    delay(15);
  }

  delay(1000); // Pausa de un segundo

  // Mueve el servo de 180 a 90 grados
  for (int pos = 180; pos >= 90; pos -= 1) {
    moverServo(pos);
    delay(15);
  }

  delay(1000); // Pausa de un segundo
}

void setup() {
  Serial.begin(115200);
  WiFi.begin(ssid, password);
  while (WiFi.status() != WL_CONNECTED) {
    delay(1000);
    Serial.println("Conectando a wifi...");
  }
  Serial.println("Conectado a wifi");

  // Imprimir la dirección IP de la ESP32
  Serial.print("Dirección IP de la ESP32: ");
  Serial.println(WiFi.localIP());

  pinMode(servoPin, OUTPUT); // Configura el pin del servo como salida

  // Configura el servidor web para activar el servo en la ruta "/motor"
  server.on("/motor", HTTP_GET, []() {
    giro(0, 0, 0); // Llama a la función `giro` para mover el servo
    server.send(200, "text/plain", "Servo controlado");
  });

  server.begin();
}

void loop() {
  server.handleClient(); // Maneja las solicitudes del cliente

  // Verifica el monitor serial
  if (Serial.available() > 0) {
    String command = Serial.readStringUntil('\n'); // Lee el comando del serial
    command.trim(); // Elimina espacios o saltos de línea
    
    if (command == "run") { // Si el comando es "run"
      Serial.println("Ejecutando movimiento del servo...");
      giro(0, 0, 0); // Llama a la función `giro` para mover el servo
      Serial.println("Movimiento completado.");
    }
  }
}
