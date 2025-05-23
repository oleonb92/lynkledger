import { useState, useEffect } from 'react';
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
  Grid,
  CircularProgress,
  Link as MuiLink,
  useTheme,
} from '@mui/material';
import { Visibility, VisibilityOff } from '@mui/icons-material';
import { motion } from 'framer-motion';
import api from '../../services/api/axios';
import { RegisterFormValues } from '../../types/auth';

const glassStyle = {
  background: 'rgba(36, 40, 47, 0.85)',
  boxShadow: '0 4px 24px 0 rgba(0,0,0,0.12)',
  backdropFilter: 'blur(6px)',
  WebkitBackdropFilter: 'blur(6px)',
  borderRadius: 28,
  border: '1px solid rgba(255,255,255,0.10)',
  padding: '3.5rem 2.5rem 3rem 2.5rem',
  maxWidth: 420,
  minHeight: 600,
  margin: '0 auto',
  display: 'flex',
  flexDirection: 'column',
  alignItems: 'center',
  justifyContent: 'center',
};

const Register = () => {
  const navigate = useNavigate();
  const [showPassword, setShowPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);
  const [loading, setLoading] = useState(false);
  const theme = useTheme();
  const [inviteEmail, setInviteEmail] = useState<string | null>(null);
  const [inviteOrgName, setInviteOrgName] = useState<string | null>(null);

  // Sincronizar inviteEmail y inviteOrgName con localStorage al montar
  useEffect(() => {
    const email = localStorage.getItem('pendingInviteEmail');
    if (email) {
      setInviteEmail(email);
      formik.setFieldValue('email', email);
    }
    const orgName = localStorage.getItem('pendingInviteOrgName');
    if (orgName) {
      setInviteOrgName(orgName);
      formik.setFieldValue('organizationName', orgName);
    }
    // eslint-disable-next-line
  }, []);

  const formik = useFormik<RegisterFormValues>({
    initialValues: {
      firstName: '',
      lastName: '',
      email: '',
      password: '',
      confirmPassword: '',
      organizationName: '',
    },
    validationSchema: Yup.object({
      firstName: Yup.string().required('El nombre es requerido'),
      lastName: Yup.string().required('El apellido es requerido'),
      email: Yup.string().email('Correo electrónico inválido').required('El correo electrónico es requerido'),
      password: Yup.string().min(8, 'La contraseña debe tener al menos 8 caracteres').required('La contraseña es requerida'),
      confirmPassword: Yup.string().oneOf([Yup.ref('password')], 'Las contraseñas deben coincidir').required('Confirma tu contraseña'),
      organizationName: Yup.string().required('El nombre de la organización es requerido'),
    }),
    onSubmit: async (values, { setStatus }) => {
      setLoading(true);
      const requestData = {
        username: values.email,
        email: values.email,
        password: values.password,
        confirm_password: values.confirmPassword,
        first_name: values.firstName,
        last_name: values.lastName,
        phone_number: '',
        language: 'en',
        timezone: Intl.DateTimeFormat().resolvedOptions().timeZone,
        account_type: 'personal',
        organization_name: values.organizationName
      };
      
      console.log('Sending registration data:', requestData);
      
      try {
        const response = await api.post('/register/', requestData);
        console.log('Registration response:', response.data);
        // Redirección inteligente para invitación pendiente
        const pendingToken = localStorage.getItem('pendingInviteToken');
        if (pendingToken) {
          localStorage.removeItem('pendingInviteToken');
          localStorage.removeItem('pendingInviteEmail');
          navigate(`/accept-invite/${pendingToken}`);
        } else {
          localStorage.removeItem('pendingInviteEmail');
          navigate('/login', {
            state: { message: 'Registro exitoso. Por favor inicia sesión.' },
          });
        }
      } catch (error: any) {
        let errorMessage = 'Error al registrar usuario';
        if (error.response?.data) {
          if (typeof error.response.data === 'object') {
            // Personaliza los mensajes más comunes
            const customMessages: Record<string, string> = {
              "user with this email already exists.": "Ya existe una cuenta registrada con este correo electrónico.",
              "A user with that username already exists.": "Ya existe una cuenta registrada con este correo electrónico.",
              "Passwords don't match": "Las contraseñas no coinciden.",
            };
            errorMessage = Object.entries(error.response.data)
              .map(([field, messages]) => {
                const msgArr = Array.isArray(messages) ? messages : [messages];
                return msgArr
                  .map(msg => customMessages[msg] || `${field}: ${msg}`)
                  .join(' | ');
              })
              .join(' | ');
          } else {
            errorMessage = error.response.data.detail || error.response.data.message || error.response.data.error || error.message;
          }
        } else {
          errorMessage = error.message;
        }
        console.error('Registration error details:', error.response?.data);
        setStatus(errorMessage);
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
            Create Account
          </Typography>
          <form onSubmit={formik.handleSubmit} autoComplete="off">
            <Grid container spacing={2}>
              <Grid item xs={12} sm={6}>
                <TextField
                  fullWidth
                  id="firstName"
                  name="firstName"
                  label="Name"
                  value={formik.values.firstName}
                  onChange={formik.handleChange}
                  onBlur={formik.handleBlur}
                  error={formik.touched.firstName && Boolean(formik.errors.firstName)}
                  helperText={formik.touched.firstName && formik.errors.firstName}
                  variant="filled"
                  InputProps={{ style: { background: 'rgba(255,255,255,0.04)' } }}
                />
              </Grid>
              <Grid item xs={12} sm={6}>
                <TextField
                  fullWidth
                  id="lastName"
                  name="lastName"
                  label="Last name"
                  value={formik.values.lastName}
                  onChange={formik.handleChange}
                  onBlur={formik.handleBlur}
                  error={formik.touched.lastName && Boolean(formik.errors.lastName)}
                  helperText={formik.touched.lastName && formik.errors.lastName}
                  variant="filled"
                  InputProps={{ style: { background: 'rgba(255,255,255,0.04)' } }}
                />
              </Grid>
              <Grid item xs={12}>
                <TextField
                  fullWidth
                  id="email"
                  name="email"
                  label="Email"
                  value={inviteEmail !== null ? inviteEmail : formik.values.email}
                  onChange={formik.handleChange}
                  onBlur={formik.handleBlur}
                  error={formik.touched.email && Boolean(formik.errors.email)}
                  helperText={formik.touched.email && formik.errors.email}
                  margin="normal"
                  variant="filled"
                  InputProps={{ 
                    style: { background: 'rgba(255,255,255,0.04)' },
                    readOnly: Boolean(inviteEmail),
                    disabled: Boolean(inviteEmail)
                  }}
                />
              </Grid>
              <Grid item xs={12}>
                <TextField
                  fullWidth
                  id="organizationName"
                  name="organizationName"
                  label="Name of the Organization"
                  value={inviteOrgName !== null ? inviteOrgName : formik.values.organizationName}
                  onChange={formik.handleChange}
                  onBlur={formik.handleBlur}
                  error={formik.touched.organizationName && Boolean(formik.errors.organizationName)}
                  helperText={formik.touched.organizationName && formik.errors.organizationName}
                  variant="filled"
                  InputProps={{ 
                    style: { background: 'rgba(255,255,255,0.04)' },
                    readOnly: Boolean(inviteOrgName),
                    disabled: Boolean(inviteOrgName)
                  }}
                />
              </Grid>
              <Grid item xs={12}>
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
              </Grid>
              <Grid item xs={12}>
                <TextField
                  fullWidth
                  id="confirmPassword"
                  name="confirmPassword"
                  label="Confirm Password"
                  type={showConfirmPassword ? 'text' : 'password'}
                  value={formik.values.confirmPassword}
                  onChange={formik.handleChange}
                  onBlur={formik.handleBlur}
                  error={formik.touched.confirmPassword && Boolean(formik.errors.confirmPassword)}
                  helperText={formik.touched.confirmPassword && formik.errors.confirmPassword}
                  variant="filled"
                  InputProps={{
                    style: { background: 'rgba(255,255,255,0.04)' },
                    endAdornment: (
                      <InputAdornment position="end">
                        <IconButton
                          aria-label="toggle password visibility"
                          onClick={() => setShowConfirmPassword(!showConfirmPassword)}
                          edge="end"
                          sx={{ color: '#b0b3b8' }}
                        >
                          {showConfirmPassword ? <VisibilityOff /> : <Visibility />}
                        </IconButton>
                      </InputAdornment>
                    ),
                  }}
                />
              </Grid>
            </Grid>

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
              {loading ? 'Registering...' : 'Register'}
            </Button>

            <MuiLink
              component="button"
              onClick={() => navigate('/login')}
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
              Already have an account? Sign in
            </MuiLink>
          </form>
        </Box>
      </motion.div>
    </Box>
  );
};

export default Register; 