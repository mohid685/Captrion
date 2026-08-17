import { Box, Flex, Spinner, Stack, Text } from '@chakra-ui/react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { useAuth } from './context/AuthContext';
import { AuthProvider } from './context/AuthContext';
import Header from './components/Header';
import Footer from './components/Footer';
import LoginPage from './pages/LoginPage';
import RegisterPage from './pages/RegisterPage';
import DashboardPage from './pages/DashboardPage';
import ChatPage from './pages/ChatPage';
import PortfolioPage from './pages/PortfolioPage';
import './App.css';

function AppContent() {
  const { currentUser, isLoading } = useAuth();

  if (isLoading) {
    return (
      <Box
        minH="100vh"
        bg="surface.DEFAULT"
        display="flex"
        alignItems="center"
        justifyContent="center"
      >
        <Stack spacing={4} align="center">
          <Spinner size="xl" color="brand.400" thickness="3px" />
          <Text color="gray.400" fontSize="lg">Loading Captrion...</Text>
        </Stack>
      </Box>
    );
  }

  return (
    <BrowserRouter>
      <Flex minH="100vh" className="app-shell" direction="column">
        <Box className="ambient blob-one" />
        <Box className="ambient blob-two" />
        <Box className="ambient blob-three" />
        <Header currentUser={currentUser} />
        <Box flex="1" width="100%" maxW="container.xl" mx="auto" px={{ base: 4, md: 6 }} py={{ base: 5, md: 7 }} zIndex={1}>
          <Routes>
            <Route path="/" element={currentUser ? <DashboardPage /> : <Navigate to="/login" replace />} />
            <Route path="/login" element={!currentUser ? <LoginPage /> : <Navigate to="/" replace />} />
            <Route path="/register" element={!currentUser ? <RegisterPage /> : <Navigate to="/" replace />} />
            <Route path="/dashboard" element={currentUser ? <DashboardPage /> : <Navigate to="/login" replace />} />
            <Route path="/chat" element={currentUser ? <ChatPage /> : <Navigate to="/login" replace />} />
            <Route path="/portfolio" element={currentUser ? <PortfolioPage /> : <Navigate to="/login" replace />} />
            <Route
              path="*"
              element={
                <Box p={8} textAlign="center" color="gray.400">
                  404 - Page not found
                </Box>
              }
            />
          </Routes>
        </Box>
        <Footer />
      </Flex>
    </BrowserRouter>
  );
}

function App() {
  return (
    <AuthProvider>
      <AppContent />
    </AuthProvider>
  );
}

export default App;
