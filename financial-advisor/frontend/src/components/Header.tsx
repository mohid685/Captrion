import { Box, Button, Flex, Text } from '@chakra-ui/react';
import { useAuth } from '../context/AuthContext';
import { useNavigate } from 'react-router-dom';
import captrionLogo from '../../logo/logo_C.png';

interface HeaderProps {
  currentUser: { email: string } | null;
}

const Header = ({ currentUser }: HeaderProps) => {
  const { logout } = useAuth();
  const navigate = useNavigate();

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  return (
    <Box
      bg="rgba(3,10,18,0.78)"
      backdropFilter="blur(12px)"
      px={6}
      py={4}
      borderBottom="1px solid"
      borderColor="rgba(82,190,244,.22)"
      position="sticky"
      top={0}
      zIndex={10}
    >
      <Flex align="center" justify="space-between" flexWrap="wrap" gap={4} maxW="container.xl" mx="auto">
        <Flex align="center" gap={3} cursor="pointer" onClick={() => navigate('/')}>
          <Box
            w={9}
            h={9}
            borderRadius="lg"
            overflow="hidden"
            bg="#04111c"
            display="flex"
            alignItems="center"
            justifyContent="center"
            fontWeight="bold"
            fontSize="lg"
            color="white"
          >
            <Box as="img" src={captrionLogo} alt="Captrion" w="100%" h="100%" objectFit="cover" transform="scale(1.45)" />
          </Box>
          <Text
            fontSize="xl"
            fontWeight="bold"
            color="white"
            textShadow="0 0 18px rgba(43,188,255,.55)"
          >
            Captrion
          </Text>
        </Flex>

        <Flex align="center" gap={{ base: 3, md: 5 }}>
          {currentUser ? (
            <>
              <Text fontSize="sm" color="gray.400" display={{ base: 'none', sm: 'block' }}>
                {currentUser.email}
              </Text>
              <Button variant="outline" borderColor="rgba(78,190,245,.55)" color="blue.100" _hover={{ bg: 'rgba(43,188,255,.12)', borderColor: 'blue.300' }} onClick={handleLogout} size="sm">
                Logout
              </Button>
            </>
          ) : (
            <>
              <Button
                bgGradient="linear(to-r, #0b78c8, #075ca0)"
                color="white"
                _hover={{ bgGradient: 'linear(to-r, brand.400, brand.500)' }}
                onClick={() => navigate('/login')}
                size="sm"
              >
                Login
              </Button>
              <Button variant="outline" borderColor="rgba(78,190,245,.55)" color="blue.100" _hover={{ bg: 'rgba(43,188,255,.12)', borderColor: 'blue.300' }} onClick={() => navigate('/register')} size="sm">
                Register
              </Button>
            </>
          )}
        </Flex>
      </Flex>
    </Box>
  );
};

export default Header;
