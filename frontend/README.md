# Getting Started with Create React App

This project was bootstrapped with [Create React App](https://github.com/facebook/create-react-app).

## Available Scripts

In the project directory, you can run:

### `npm start`

Runs the app in the development mode.\
Open [http://localhost:3000](http://localhost:3000) to view it in the browser.

The page will reload if you make edits.\
You will also see any lint errors in the console.

### `npm test`

Launches the test runner in the interactive watch mode.\
See the section about [running tests](https://facebook.github.io/create-react-app/docs/running-tests) for more information.

### `npm run build`

Builds the app for production to the `build` folder.\
It correctly bundles React in production mode and optimizes the build for the best performance.

The build is minified and the filenames include the hashes.\
Your app is ready to be deployed!

See the section about [deployment](https://facebook.github.io/create-react-app/docs/deployment) for more information.

### `npm run eject`

**Note: this is a one-way operation. Once you `eject`, you can't go back!**

If you aren't satisfied with the build tool and configuration choices, you can `eject` at any time. This command will remove the single build dependency from your project.

Instead, it will copy all the configuration files and the transitive dependencies (webpack, Babel, ESLint, etc) right into your project so you have full control over them. All of the commands except `eject` will still work, but they will point to the copied scripts so you can tweak them. At this point you're on your own.

You don't have to ever use `eject`. The curated feature set is suitable for small and middle deployments, and you shouldn't feel obligated to use this feature. However we understand that this tool wouldn't be useful if you couldn't customize it when you are ready for it.

## Learn More

You can learn more in the [Create React App documentation](https://facebook.github.io/create-react-app/docs/getting-started).

To learn React, check out the [React documentation](https://reactjs.org/).

## Visión y mejores prácticas para el frontend

- Tema oscuro por defecto y diseño elegante
- Uso de Material UI v5+ con personalización avanzada
- Animaciones suaves con Framer Motion
- Formularios robustos con React Hook Form o Formik + Yup/Zod
- Tipografía moderna (Inter, Roboto)
- Accesibilidad y responsividad total
- Seguridad: validación fuerte, protección XSS/CSRF, headers seguros
- Lazy loading de componentes y rutas
- Optimización de imágenes y SVGs
- Uso de SWR o React Query para manejo de datos (futuro)
- Helmet para headers/meta de seguridad

### Ejemplo de theme oscuro en MUI

```ts
import { createTheme } from '@mui/material/styles';

const theme = createTheme({
  palette: {
    mode: 'dark',
    primary: { main: '#00bcd4' },
    secondary: { main: '#ff4081' },
    background: { default: '#181a20', paper: '#23272f' },
    text: { primary: '#fff', secondary: '#b0b3b8' },
  },
  typography: {
    fontFamily: 'Inter, Roboto, Arial, sans-serif',
  },
  shape: {
    borderRadius: 12,
  },
});

export default theme;
```

> El objetivo es que la experiencia de usuario sea moderna, rápida, segura y elegante, pensando siempre en la escalabilidad y el futuro del producto.
