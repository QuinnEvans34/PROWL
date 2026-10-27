import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import { fileURLToPath } from 'node:url'
const proxy = () => ({target:'http://127.0.0.1:8020',changeOrigin:true,configure(p){
  // Isolated fixture only: backend sees its own loopback host. Production policy stays unchanged.
  p.on('proxyReq', req => req.removeHeader('origin'))
}})
export default defineConfig({root:fileURLToPath(new URL('./reviewer-walkthrough',import.meta.url)),publicDir:false,plugins:[react()],
 server:{host:'127.0.0.1',port:5186,strictPort:true,open:false,fs:{allow:[fileURLToPath(new URL('../..',import.meta.url))]},
 proxy:{'/review-records':proxy(),'/walkthrough-identity':proxy()}}})
