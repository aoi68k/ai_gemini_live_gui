using System;
using System.IO;
using System.Net;
using System.Runtime.InteropServices;
using System.Speech.Synthesis.TtsEngine;
using System.Text;

namespace GeminiSpeechSapi
{
    [Guid("F623F7E3-125A-4A73-90BD-7E05C5E784D1")]
    [ComVisible(true)]
    public class GeminiTtsEngine : TtsEngineSsml
    {
        private string logFile = @"C:\Users\aoi68\.gemini\antigravity\brain\794fa98f-f0c6-4076-9e7b-e73bcf8e5f9c\scratch\sapi_log.txt";

        public GeminiTtsEngine() : base("")
        {
            Log("GeminiTtsEngine constructed.");
        }

        private void Log(string message)
        {
            try
            {
                File.AppendAllText(logFile, string.Format("[{0:HH:mm:ss}] {1}\n", DateTime.Now, message));
            }
            catch {}
        }

        public override void Speak(TextFragment[] fragment, IntPtr waveHeader, ITtsEngineSite site)
        {
            Log("Speak called.");
            try
            {
                StringBuilder textBuilder = new StringBuilder();
                foreach (var frag in fragment)
                {
                    textBuilder.Append(frag.TextToSpeak);
                }

                string textToSpeak = textBuilder.ToString().Trim();
                Log(string.Format("Text to speak: {0}", textToSpeak));
                
                if (string.IsNullOrEmpty(textToSpeak))
                {
                    Log("Text is empty. Returning.");
                    return;
                }

                string url = "http://127.0.0.1:50022/synthesis?speaker=0";
                string queryUrl = "http://127.0.0.1:50022/audio_query?text=" + Uri.EscapeDataString(textToSpeak) + "&speaker=0";
                string queryJson = "";
                
                Log("Fetching audio_query...");
                using (WebClient wc = new WebClient())
                {
                    wc.Encoding = Encoding.UTF8;
                    queryJson = wc.UploadString(queryUrl, "POST", "");
                }
                Log("audio_query fetched.");

                byte[] wavBytes = null;
                Log("Fetching synthesis...");
                using (WebClient wc = new WebClient())
                {
                    wc.Headers[HttpRequestHeader.ContentType] = "application/json";
                    wavBytes = wc.UploadData(url, "POST", Encoding.UTF8.GetBytes(queryJson));
                }
                Log(string.Format("synthesis fetched, {0} bytes.", wavBytes.Length));

                if (wavBytes != null && wavBytes.Length > 44)
                {
                    int dataLength = wavBytes.Length - 44;
                    byte[] pcmData = new byte[dataLength];
                    Array.Copy(wavBytes, 44, pcmData, 0, dataLength);

                    Log(string.Format("Writing {0} PCM bytes to site...", dataLength));
                    GCHandle pinnedArray = GCHandle.Alloc(pcmData, GCHandleType.Pinned);
                    IntPtr pointer = pinnedArray.AddrOfPinnedObject();
                    try
                    {
                        site.Write(pointer, dataLength);
                        Log("site.Write successful.");
                    }
                    finally
                    {
                        pinnedArray.Free();
                    }
                }
            }
            catch (Exception ex)
            {
                Log(string.Format("Exception in Speak: {0}\n{1}", ex.Message, ex.StackTrace));
            }
        }

        public override IntPtr GetOutputFormat(SpeakOutputFormat format, IntPtr targetWaveFormat)
        {
            Log("GetOutputFormat called.");
            try 
            {
                // Always return our specific format (24000Hz 16-bit Mono) so SAPI5 can automatically resample if needed.
                short channels = 1;
                int samplesPerSec = 24000;
                short bitsPerSample = 16;
                short blockAlign = (short)(channels * (bitsPerSample / 8));
                int averageBytesPerSec = samplesPerSec * blockAlign;

                IntPtr formatPtr = Marshal.AllocCoTaskMem(18);
                Marshal.WriteInt16(formatPtr, 0, 1); // wFormatTag = WAVE_FORMAT_PCM
                Marshal.WriteInt16(formatPtr, 2, channels); // nChannels
                Marshal.WriteInt32(formatPtr, 4, samplesPerSec); // nSamplesPerSec
                Marshal.WriteInt32(formatPtr, 8, averageBytesPerSec); // nAvgBytesPerSec
                Marshal.WriteInt16(formatPtr, 12, blockAlign); // nBlockAlign
                Marshal.WriteInt16(formatPtr, 14, bitsPerSample); // wBitsPerSample
                Marshal.WriteInt16(formatPtr, 16, 0); // cbSize

                Log("GetOutputFormat returned properly allocated WAVEFORMATEX.");
                return formatPtr;
            }
            catch (Exception ex)
            {
                Log(string.Format("Exception in GetOutputFormat: {0}", ex.Message));
                return targetWaveFormat;
            }
        }

        public override void AddLexicon(Uri uri, string mediaType, ITtsEngineSite site)
        {
            Log("AddLexicon called.");
        }

        public override void RemoveLexicon(Uri uri, ITtsEngineSite site)
        {
            Log("RemoveLexicon called.");
        }
    }
}
