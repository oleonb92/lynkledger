import { createTheme, PaletteOptions } from '@mui/material/styles';

// Paleta centralizada para fácil cambio de tema
const paletteDark: PaletteOptions = {
  mode: 'dark',
  primary: { main: '#00bcd4' },
  secondary: { main: '#ff4081' },
  background: {
    default: '#181A20', // fondo principal muy oscuro
    paper: '#23272F',   // cards más claras
  },
  text: {
    primary: '#F5F6FA',
    secondary: '#A0A4B8',
  },
};

// Si quieres modo claro, define aquí otra paleta y alterna con un context/provider
// const paletteLight = { ... };

const theme = createTheme({
  palette: paletteDark,
  typography: {
    fontFamily: 'Inter, Roboto, Arial, sans-serif',
  },
  shape: {
    borderRadius: 6,
  },
  components: {
    MuiButton: {
      styleOverrides: {
        root: {
          textTransform: 'none',
          borderRadius: 6,
        },
      },
    },
    MuiCard: {
      styleOverrides: {
        root: {
          borderRadius: 6,
          background: 'rgba(35,39,47,0.96)',
          border: '1px solid rgba(255,255,255,0.06)',
          boxShadow: '0 4px 24px 0 rgba(0,0,0,0.18)',
          color: '#F5F6FA',
        },
      },
    },
    MuiCardContent: {
      styleOverrides: {
        root: {
          background: 'transparent',
        },
      },
    },
  },
});

export default theme; 