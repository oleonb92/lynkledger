import { useParams, useNavigate } from 'react-router-dom';
import { useEffect, useState } from 'react';
import api from '../../services/api/axios';
import { Box, Typography, Button, CircularProgress, Paper } from '@mui/material';

const AcceptInvite = () => {
  const { token } = useParams();
  const navigate = useNavigate();
  const [status, setStatus] = useState<'pending'|'success'|'error'>('pending');
  const [message, setMessage] = useState('');
  const [invitationDetails, setInvitationDetails] = useState<any>(null);

  useEffect(() => {
    const fetchInvitation = async () => {
      try {
        // Primero obtenemos los detalles de la invitación
        const response = await api.get(`/invitations/${token}/`);
        setInvitationDetails(response.data);
      } catch (err: any) {
        setStatus('error');
        setMessage(err.response?.data?.detail || 'No se pudo encontrar la invitación. Puede que haya expirado o haya sido utilizada.');
      }
    };

    if (token) {
      fetchInvitation();
    } else {
      setStatus('error');
      setMessage('Token de invitación inválido.');
    }
  }, [token]);

  const handleAccept = async () => {
    try {
      await api.post(`/invitations/${token}/accept/`);
      setStatus('success');
      setMessage('¡Invitación aceptada! Ya eres miembro de la organización. Puedes iniciar sesión.');
    } catch (err: any) {
      setStatus('error');
      setMessage(err.response?.data?.detail || 'No se pudo aceptar la invitación. Puede que ya haya expirado o haya sido utilizada.');
    }
  };

  const handleGoToLogin = () => navigate('/login');

  console.log("AcceptInvite render", { status, message, invitationDetails });

  return (
    <Box minHeight="100vh" display="flex" alignItems="center" justifyContent="center" bgcolor="#181A20">
      <Paper elevation={3} sx={{ p: 4, maxWidth: 400, width: '100%', textAlign: 'center', bgcolor: '#23272F' }}>
        <Typography color="yellow" sx={{ mb: 2 }}>
          Debug: status={status}, message={message}, token={token}
        </Typography>
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