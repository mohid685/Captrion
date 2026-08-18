import { Box, Button, Flex, Text } from '@chakra-ui/react';
import { useAuth } from '../context/AuthContext';
import { useNavigate, useLocation, Link as RouterLink } from 'react-router-dom';

interface HeaderProps {
  currentUser: { email: string } | null;
}

const NAV_LINKS = [
  { label: 'Dashboard', to: '/dashboard' },
  { label: 'Chat', to: '/chat' },
  { label: 'Portfolio', to: '/portfolio' },
];

const Header = ({ currentUser }: HeaderProps) => {
  const { logout } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  const isLoginPage = location.pathname === '/login';
  const isRegisterPage = location.pathname === '/register';

  return (
    <Box
      className="app-header"
      bg="rgba(3,10,18,0.72)"
      backdropFilter="blur(14px)"
      px={6}
      py={3.5}
      position="sticky"
      top={0}
      zIndex={10}
    >
      <Flex align="center" justify="space-between" flexWrap="wrap" gap={4} maxW="container.xl" mx="auto" position="relative">
        <Flex align="center" gap={3} cursor="pointer" onClick={() => navigate('/')}>
          <Text
            fontSize="2xl"
            fontWeight="bold"
            color="white"
            textShadow="0 0 18px rgba(43,188,255,.55)"
          >
            Captrion
          </Text>
        </Flex>

        {currentUser && (
          <Flex
            as="nav"
            align="center"
            gap={1}
            display={{ base: 'none', md: 'flex' }}
            position="absolute"
            left="50%"
            transform="translateX(-50%)"
          >
            {NAV_LINKS.map((link) => {
              const active = location.pathname === link.to;
              return (
                <Box
                  key={link.to}
                  as={RouterLink}
                  to={link.to}
                  position="relative"
                  px={3}
                  py={2}
                  fontSize="sm"
                  fontWeight="600"
                  color={active ? 'white' : 'gray.400'}
                  transition="color .18s ease"
                  _hover={{ color: 'white' }}
                >
                  {link.label}
                  <Box
                    position="absolute"
                    left={3}
                    right={3}
                    bottom={0}
                    h="2px"
                    borderRadius="full"
                    bg="brand.400"
                    opacity={active ? 1 : 0}
                    boxShadow={active ? '0 0 10px rgba(43,188,255,.8)' : 'none'}
                    transition="opacity .18s ease"
                  />
                </Box>
              );
            })}
          </Flex>
        )}

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
          ) : isLoginPage ? (
            <Button variant="outline" borderColor="rgba(78,190,245,.55)" color="blue.100" _hover={{ bg: 'rgba(43,188,255,.12)', borderColor: 'blue.300' }} onClick={() => navigate('/register')} size="sm">
              Register
            </Button>
          ) : isRegisterPage ? (
            <Button
              bgGradient="linear(to-r, #0b78c8, #075ca0)"
              color="white"
              _hover={{ bgGradient: 'linear(to-r, brand.400, brand.500)' }}
              onClick={() => navigate('/login')}
              size="sm"
            >
              Login
            </Button>
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