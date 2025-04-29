import clsx from 'clsx';
import Heading from '@theme/Heading';
import styles from './styles.module.css';

// Import PNG images
import ImgAI from '@site/static/img/undraw_artificial_intelligence.png';
import ImgUpload from '@site/static/img/undraw_upload.png';
import ImgQuestions from '@site/static/img/undraw_questions.png';
import ImgFiles from '@site/static/img/undraw_folder_files.png';
import ImgBugFix from '@site/static/img/undraw_bug_fixing.png';
import ImgWebDev from '@site/static/img/undraw_web_development.png';

const FeatureList = [
  {
    title: 'Flexible AI Content Generation',
    Img: ImgAI,
    description: (
      <>
        Generate diverse content — from simple answers to complex structured data — using Gemini's advanced AI, with full prompt customization and retry mechanisms.
      </>
    ),
  },
  {
    title: 'Audio Upload and YouTube Integration',
    Img: ImgUpload,
    description: (
      <>
        Upload audio files directly or extract audio from YouTube links. Transcribe them into clean text using a Whisper-powered backend, with smart segmentation.
      </>
    ),
  },
  {
    title: 'High-Quality Question Generation',
    Img: ImgQuestions,
    description: (
      <>
        Bulk-generate multiple types of questions (MTL, SML, OTL, SOL) with detailed solutions. Outputs are structured into easily parsable JSON format for downstream use.
      </>
    ),
  },
  {
    title: 'Robust File Management System',
    Img: ImgFiles,
    description: (
      <>
        Manage file uploads, downloads, transcripts, and generated content seamlessly. Supports error feedback, metadata attachment, and session-based storage.
      </>
    ),
  },
  {
    title: 'Smart Retry and Error Handling',
    Img: ImgBugFix,
    description: (
      <>
        Automatically detect failed generations or transcriptions and retry with adaptive techniques, ensuring a high success rate across all operations.
      </>
    ),
  },
  {
    title: 'Fast and Extensible Frontend & Backend',
    Img: ImgWebDev,
    description: (
      <>
        Built with React, Flask, and scalable APIs. Designed to be fast, extendable, and easily customizable for future AI integration or feature upgrades.
      </>
    ),
  },
];

function Feature({Img, title, description}) {
  return (
    <div className={clsx('col col--4')}>
      <div className="text--center">
        <img src={Img} alt={title} className={styles.featureImg} />
      </div>
      <div className="text--center padding-horiz--md">
        <Heading as="h3">{title}</Heading>
        <p>{description}</p>
      </div>
    </div>
  );
}

export default function HomepageFeatures() {
  return (
    <section className={styles.features}>
      <div className="container">
        <div className="row">
          {FeatureList.map((props, idx) => (
            <Feature key={idx} {...props} />
          ))}
        </div>
      </div>
    </section>
  );
}
