import { useParams, useNavigate } from 'react-router-dom';
import { useEffect, useState } from 'react';
import api from '../../services/api/axios';
import { Box, Typography, Button, CircularProgress, Paper } from '@mui/material';
import { useAppSelector } from '../../store';

const AcceptInvite = () => {
  const { token } = useParams();
  const navigate = useNavigate();
  const { isAuthenticated } = useAppSelector((state) => state.auth);
  const [status, setStatus] = useState<'pending'|'success'|'error'>('pending');
  const [message, setMessage] = useState('');
  const [invitationDetails, setInvitationDetails] = useState<any>(null);

  useEffect(() => {
    if (!token) {
      setStatus('error');
      setMessage('Token de invitación inválido.');
      return;
    }
    // Si no autenticado, guardar token en localStorage
    if (!isAuthenticated && token) {
      localStorage.setItem('pendingInviteToken', token);
    }
    const fetchInvitation = async () => {
      try {
        const response = await api.get(`/invitations/${token}/`);
        setInvitationDetails(response.data);
        // Si no autenticado, guardar email de invitación
        if (!isAuthenticated && response.data?.email) {
          localStorage.setItem('pendingInviteEmail', response.data.email);
        }
        if (!isAuthenticated && response.data?.organization_name) {
          localStorage.setItem('pendingInviteOrgName', response.data.organization_name);
        }
      } catch (err: any) {
        setStatus('error');
        setMessage(err.response?.data?.detail || 'No se pudo encontrar la invitación. Puede que haya expirado o haya sido utilizada.');
      }
    };
    fetchInvitation();
  }, [token, isAuthenticated]);

  const handleAccept = async () => {
    try {
      await api.post(`/invitations/${token}/accept/`);
      setStatus('success');
      setMessage('¡Invitación aceptada! Ya eres miembro de la organización. Puedes iniciar sesión.');
      localStorage.removeItem('pendingInviteToken');
    } catch (err: any) {
      setStatus('error');
      setMessage(err.response?.data?.detail || 'No se pudo aceptar la invitación. Puede que ya haya expirado o haya sido utilizada.');
    }
  };

  const handleGoToLogin = () => navigate('/login');
  const handleGoToRegister = () => navigate('/register');

  // Si no autenticado, mostrar mensaje y botones
  if (!isAuthenticated) {
    return (
      <Box minHeight="100vh" display="flex" alignItems="center" justifyContent="center" bgcolor="#181A20">
        <Paper elevation={3} sx={{ p: 4, maxWidth: 400, width: '100%', textAlign: 'center', bgcolor: '#23272F' }}>
          <Typography variant="h5" color="primary" gutterBottom>
            Aceptar invitación
          </Typography>
          <Typography variant="body1" color="white" gutterBottom>
            Debes iniciar sesión o registrarte para aceptar la invitación.<br />
            Guarda este enlace o vuelve a hacer clic después de autenticarte.
          </Typography>
          <Button variant="contained" color="primary" onClick={handleGoToLogin} sx={{ mt: 2, mr: 1 }}>
            Iniciar sesión
          </Button>
          <Button variant="outlined" color="primary" onClick={handleGoToRegister} sx={{ mt: 2 }}>
            Registrarse
          </Button>
        </Paper>
      </Box>
    );
  }

  // Si autenticado, flujo normal
  return (
    <Box minHeight="100vh" display="flex" alignItems="center" justifyContent="center" bgcolor="#181A20">
      <Paper elevation={3} sx={{ p: 4, maxWidth: 400, width: '100%', textAlign: 'center', bgcolor: '#23272F' }}>
        <Typography variant="h5" color="primary" gutterBottom>
          Aceptar invitación
        </Typography>
        {status === 'pending' && (
          <>
            {invitationDetails ? (
              <>
                <Typography variant="body1" color="white" gutterBottom>
                  Has sido invitado a unirte a <strong>{invitationDetails.organization_name}</strong> como <strong>{invitationDetails.role}</strong>
                </Typography>
                <Button 
                  variant="contained" 
                  color="primary" 
                  onClick={handleAccept}
                  sx={{ mt: 2 }}
                >
                  Aceptar invitación
                </Button>
              </>
            ) : (
              <CircularProgress color="primary" />
            )}
          </>
        )}
        {status === 'success' && (
          <>
            <Typography variant="body1" color="success.main" gutterBottom>{message}</Typography>
            <Button variant="contained" color="primary" onClick={handleGoToLogin} sx={{ mt: 2 }}>
              Ir a iniciar sesión
            </Button>
          </>
        )}
        {status === 'error' && (
          <>
            <Typography variant="body1" color="error" gutterBottom>{message}</Typography>
            <Button variant="contained" color="primary" onClick={handleGoToLogin} sx={{ mt: 2 }}>
              Ir a iniciar sesión
            </Button>
          </>
        )}
      </Paper>
    </Box>
  );
};

export default AcceptInvite; 