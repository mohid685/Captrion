import { Box, Button, FormControl, Input, Text, useToast, VStack } from '@chakra-ui/react';
import { useAuth } from '../context/AuthContext';
import { useNavigate } from 'react-router-dom';
import { useState } from 'react';
import type { FormEvent } from 'react';

const RegisterPage = () => {
  const { register } = useAuth();
  const navigate = useNavigate();
  const toast = useToast();

  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    if (!email || !password) {
      toast({ title: 'Please fill in all fields', status: 'error', duration: 3000, isClosable: true });
      return;
    }
    if (!/^\S+@\S+\.\S+$/.test(email)) {
      toast({ title: 'Enter a valid email address', status: 'error', duration: 3000, isClosable: true });
      return;
    }
    if (password.length < 8) {
      toast({ title: 'Your password must be at least 8 characters', status: 'error', duration: 3000, isClosable: true });
      return;
    }

    setLoading(true);
    try {
      await register(email, password);
      toast({ title: 'Registration successful', status: 'success', duration: 3000, isClosable: true });
      navigate('/login');
    } catch (error: any) {
      toast({ title: error.message || 'Registration failed', status: 'error', duration: 3000, isClosable: true });
    } finally {
      setLoading(false);
    }
  };

  return (
    <VStack className="auth-shell" align="flex-start" justify="center" spacing={6} p={8}>
      <Box className="auth-heading"><Text className="eyebrow">Secure access</Text><Text fontSize={{ base: '3xl', md: '4xl' }} fontWeight="800" className="page-title">Create account</Text><Text fontSize="md" color="gray.400" mt={2}>Set up your workspace.</Text></Box>
      <Box
        className="auth-card glass"
        w="100%"
        maxW="md"
      >
        <Text fontSize="2xl" fontWeight="bold" mb={6} color="white" textAlign="center">
          Account details
        </Text>
        <form onSubmit={handleSubmit}>
          <VStack spacing={4} align="stretch">
            <FormControl isRequired>
              <Input
                type="email"
                placeholder="Enter your email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                size="lg"
              />
            </FormControl>
            <FormControl isRequired>
              <Input
                type="password"
                placeholder="Create a password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                size="lg"
              />
            </FormControl>
            <Button
              w="100%"
              mt={2}
              size="lg"
              bgGradient="linear(to-r, brand.500, brand.600)"
              color="white"
              _hover={{ bgGradient: 'linear(to-r, brand.400, brand.600)' }}
              isLoading={loading}
              type="submit"
            >
              Register
            </Button>
          </VStack>
          <Text mt={5} fontSize="sm" color="gray.500" textAlign="center">
            Already have an account?{' '}
            <Text
              as="span"
              color="brand.300"
              cursor="pointer"
              fontWeight="semibold"
              onClick={() => navigate('/login')}
            >
              Login here
            </Text>
          </Text>
        </form>
      </Box>
    </VStack>
  );
};

export default RegisterPage;
