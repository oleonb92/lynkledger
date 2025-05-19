FROM node:18-alpine

WORKDIR /app

# Instalar dependencias globales necesarias
RUN npm install -g npm@latest

# Copiar solo los archivos necesarios para la instalación de dependencias
COPY package*.json ./

# Instalar dependencias con flags para optimizar
RUN npm ci --only=production --no-audit --no-optional

# Copiar el resto de los archivos
COPY . .

# Exponer el puerto
EXPOSE 3000

# Comando para iniciar la aplicación
CMD ["npm", "start"]