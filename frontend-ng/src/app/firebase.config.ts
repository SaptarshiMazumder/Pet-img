import { initializeApp } from 'firebase/app';

const firebaseConfig = {
  apiKey: 'AIzaSyB68cI5a2ZLH-RNDS-MrsuM-g2t9JM-YJY',
  authDomain: 'pet-gen-dev.firebaseapp.com',
  projectId: 'pet-gen-dev',
  storageBucket: 'pet-gen-dev.firebasestorage.app',
  messagingSenderId: '85701337943',
  appId: '1:85701337943:web:099c9212c7111a91cc5412',
};
export const firebaseApp = initializeApp(firebaseConfig);
