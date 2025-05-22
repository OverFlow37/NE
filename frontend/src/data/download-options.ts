import { DownloadOption, SystemRequirement } from '@/types';

export const downloadOptions: DownloadOption[] = [
  {
    id: '1',
    platform: 'windows',
    version: '1.0.0',
    fileUrl: '/downloads/ProjectNewEden-Win-v1.0.0.zip',
    fileSize: '55 MB',
  },
  {
    id: '2',
    platform: 'macos',
    version: '1.0.0',
    fileUrl: '/downloads/ProjectNewEden-max-v1.0.0.dmg',
    fileSize: '55 MB',
  },
  {
    id: '3',
    platform: 'linux',
    version: '1.0.0',
    fileUrl: '/downloads/ProjectNewEden-linux-v1.0.0.gz',
    fileSize: '55 MB',
  },
];

export const systemRequirements: SystemRequirement[] = [
  {
    type: 'minimum',
    os: 'Windows 10',
    processor: 'Intel i5-8400 / AMD Ryzen 5 2600',
    memory: '16GB RAM',
    graphics: 'NVIDIA GTX 960 / AMD RX 570',
    storage: '10GB',
    additionalNotes: '인터넷 연결 (초기 설치 시)',
  },
  {
    type: 'recommended',
    os: 'Windows 11',
    processor: 'Intel i7-10700K / AMD Ryzen 7 5800X',
    memory: '32GB RAM',
    graphics: 'NVIDIA RTX 3060 / AMD RX 6700 XT',
    storage: 'SSD 20GB 이상',
    additionalNotes: '인터넷 연결 (초기 설치 시)',
  },
];
