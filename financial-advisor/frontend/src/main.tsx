import { createRoot } from 'react-dom/client'
import { ChakraProvider, extendTheme, type ThemeConfig } from '@chakra-ui/react'
import App from './App.tsx'
import './index.css'

const config: ThemeConfig = {
  initialColorMode: 'dark',
  useSystemColorMode: false,
}

const theme = extendTheme({
  config,
  fonts: {
    heading: `'Inter', system-ui, sans-serif`,
    body: `'Inter', system-ui, sans-serif`,
  },
  colors: {
    brand: {
      50: '#edfaff', 100: '#d6f4ff', 200: '#aee9ff', 300: '#70d8ff', 400: '#2bbcff', 500: '#0b78c8', 600: '#075ca0', 700: '#06477c', 800: '#06385f', 900: '#04243e',
    },
    surface: {
      DEFAULT: '#03080f', card: '#07131f', cardHover: '#0b1d2c', border: '#15364c',
    },
  },
  styles: {
    global: {
      body: {
        bg: '#03080f',
        color: '#e5e7ef',
      },
    },
  },
  components: {
    Button: {
      baseStyle: {
        fontWeight: '600',
        borderRadius: 'lg',
      },
    },
    Input: {
      variants: {
        outline: {
          field: {
            bg: 'surface.card',
            borderColor: 'surface.border',
            _hover: { borderColor: 'brand.400' },
            _focus: { borderColor: 'brand.400', boxShadow: '0 0 0 1px #2bbcff' },
          },
        },
      },
      defaultProps: {
        variant: 'outline',
      },
    },
  },
})

createRoot(document.getElementById('root')!).render(
  <ChakraProvider theme={theme}>
    <App />
  </ChakraProvider>,
)
