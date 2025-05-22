import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useFormik } from 'formik';
import * as Yup from 'yup';
import {
  TextField,
  Button,
  Typography,
  Box,
  Alert,
  IconButton,
  InputAdornment,
  CircularProgress,
  Link as MuiLink,
  useTheme,
} from '@mui/material';
import { Visibility, VisibilityOff } from '@mui/icons-material';
import { useAppDispatch } from '../../store';
import { loginStart, loginSuccess, loginFailure } from '../../store/slices/authSlice';
import api from '../../services/api/axios';
import { LoginFormValues } from '../../types/auth';
import { motion } from 'framer-motion';

const glassStyle = {
  background: 'rgba(36, 40, 47, 0.85)',
  boxShadow: '0 4px 24px 0 rgba(0,0,0,0.12)',
  backdropFilter: 'blur(6px)',
  WebkitBackdropFilter: 'blur(6px)',
  borderRadius: 28,
  border: '1px solid rgba(255,255,255,0.10)',
  padding: '3.5rem 2.5rem 3rem 2.5rem',
  maxWidth: 420,
  minHeight: 520,
  margin: '0 auto',
  display: 'flex',
  flexDirection: 'column',
  alignItems: 'center',
  justifyContent: 'center',
};

const Login = () => {
  const navigate = useNavigate();
  const dispatch = useAppDispatch();
  const [showPassword, setShowPassword] = useState(false);
  const [loading, setLoading] = useState(false);
  const theme = useTheme();

  const formik = useFormik<LoginFormValues>({
    initialValues: {
      email: '',
      password: '',
    },
    validationSchema: Yup.object({
      email: Yup.string().email('Correo electrónico inválido').required('El correo electrónico es requerido'),
      password: Yup.string().min(8, 'La contraseña debe tener al menos 8 caracteres').required('La contraseña es requerida'),
    }),
    onSubmit: async (values, { setStatus }) => {
      setLoading(true);
      try {
        dispatch(loginStart());
        // 1. Obtener tokens
        const response = await api.post('/token/', {
          username: values.email,
          password: values.password,
        });
        const { access, refresh } = response.data;
        console.log('Tokens recibidos:', { access, refresh });
        
        // 2. Obtener información del usuario
        const userResponse = await api.get('/users/me/', {
          headers: {
            Authorization: `Bearer ${access}`
          }
        });
        
        const userData = userResponse.data;
        console.log('Datos del usuario recibidos:', userData);
        
        // 3. Guardar tokens y datos del usuario
        localStorage.setItem('token', access);
        localStorage.setItem('refreshToken', refresh);
        
        const userToStore = {
          id: userData.id,
          email: userData.email,
          firstName: userData.first_name,
          lastName: userData.last_name,
          organizationId: userData.organization_id,
        };
        console.log('Usuario a guardar en Redux:', userToStore);
        
        dispatch(loginSuccess({
          user: userToStore,
          token: access,
          refreshToken: refresh,
        }));
        navigate('/dashboard');
      } catch (error: any) {
        console.error('Login error:', error);
        console.error('Error response:', error.response);
        setStatus(error.response?.data?.detail || error.message || 'Error al iniciar sesión');
        dispatch(loginFailure(error.response?.data?.detail || error.message || 'Error al iniciar sesión'));
      } finally {
        setLoading(false);
      }
    },
  });

  return (
    <Box sx={{ minHeight: '100vh', display: 'flex', alignItems: 'center', justifyContent: 'center', background: theme.palette.background.default }}>
      <motion.div
        initial={{ opacity: 0, y: 40 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.7, ease: 'easeOut' }}
        style={{ width: '100%' }}
      >
        <Box sx={glassStyle}>
          <Typography component="h1" variant="h5" sx={{ mb: 4, fontWeight: 700, letterSpacing: 1, color: '#fff', textAlign: 'center', wordBreak: 'break-word', maxWidth: '100%' }}>
            Welcome Back
          </Typography>
          <form onSubmit={formik.handleSubmit} autoComplete="off">
            <TextField
              fullWidth
              id="email"
              name="email"
              label="Email"
              value={formik.values.email}
              onChange={formik.handleChange}
              onBlur={formik.handleBlur}
              error={formik.touched.email && Boolean(formik.errors.email)}
              helperText={formik.touched.email && formik.errors.email}
              margin="normal"
              variant="filled"
              InputProps={{ style: { background: 'rgba(255,255,255,0.04)' } }}
            />
            <TextField
              fullWidth
              id="password"
              name="password"
              label="Password"
              type={showPassword ? 'text' : 'password'}
              value={formik.values.password}
              onChange={formik.handleChange}
              onBlur={formik.handleBlur}
              error={formik.touched.password && Boolean(formik.errors.password)}
              helperText={formik.touched.password && formik.errors.password}
              margin="normal"
              variant="filled"
              InputProps={{
                style: { background: 'rgba(255,255,255,0.04)' },
                endAdornment: (
                  <InputAdornment position="end">
                    <IconButton
                      aria-label="toggle password visibility"
                      onClick={() => setShowPassword(!showPassword)}
                      edge="end"
                      sx={{ color: '#b0b3b8' }}
                    >
                      {showPassword ? <VisibilityOff /> : <Visibility />}
                    </IconButton>
                  </InputAdornment>
                ),
              }}
            />
            {formik.status && (
              <Alert severity="error" sx={{ mt: 2 }}>
                {formik.status}
              </Alert>
            )}
            <Button
              type="submit"
              fullWidth
              variant="contained"
              sx={{
                mt: 3,
                mb: 2,
                py: 1.5,
                fontWeight: 700,
                fontSize: '1.1rem',
                background: 'linear-gradient(90deg, #00bcd4 0%, #2196f3 100%)',
                boxShadow: '0 2px 8px 0 rgba(0,188,212,0.15)',
                transition: 'transform 0.2s',
                '&:hover': {
                  background: 'linear-gradient(90deg, #2196f3 0%, #00bcd4 100%)',
                  transform: 'scale(1.03)',
                },
              }}
              disabled={formik.isSubmitting || loading}
              endIcon={loading && <CircularProgress size={22} sx={{ color: '#fff' }} />}
            >
              {loading ? 'Signing in...' : 'Sign In'}
            </Button>
            <MuiLink
              component="button"
              onClick={() => navigate('/register')}
              sx={{
                display: 'block',
                mt: 2,
                color: '#00bcd4',
                fontWeight: 500,
                fontSize: '1rem',
                textDecoration: 'underline',
                transition: 'color 0.2s',
                '&:hover': { color: '#ff4081' },
              }}
            >
              Don't have an account? Register
            </MuiLink>
          </form>
        </Box>
      </motion.div>
    </Box>
  );
};

export default Login; 