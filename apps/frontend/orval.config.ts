import { defineConfig } from 'orval';

export default defineConfig({
  resumeGenius: {
    input: {
      target: 'http://localhost:8000/openapi.json',
    },
    output: {
      mode: 'single',
      target: './src/lib/api/generated/api.ts',
      schemas: './src/lib/api/generated/schemas',
      client: 'axios-functions',
      override: {
        mutator: {
          path: './src/lib/api/orval-axios.ts',
          name: 'customAxiosInstance',
        },
      },
      prettier: true,
      tsconfig: './tsconfig.json',
    },
    hooks: {
      afterAllFilesWrite: 'node scripts/fix-orval-output.js',
    },
  },
  
  resumeGeniusZod: {
    input: {
      target: 'http://localhost:8000/openapi.json',
    },
    output: {
      mode: 'single',
      target: './src/lib/api/generated/api.zod.ts',
      client: 'zod',
      prettier: true,
    },
    hooks: {
      afterAllFilesWrite: 'node scripts/fix-orval-output.js',
    },
  },
});