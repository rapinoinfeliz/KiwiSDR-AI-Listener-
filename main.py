import time
from src.core.kiwi_adapter import KiwiSDRAdapter
from src.core.asr_engine import FasterWhisperEngine
from src.core.feature_extractor import BasicFeatureExtractor
from src.core.auto_tuner import HillClimbingAutoTuner
from src.core.queue import MemoryQueue
from src.core.workers import RadioWorker, InferenceWorker
from src.core.discovery import KiwiSDRDiscoveryService
from src.core.scheduler import BanditScheduler
from src.core.mock_adapter import MockRadioClient
import sys

def main():
    print("--- KiwiSDR AI Listener ---")
    
    # 1. Initialize dependencies
    queue = MemoryQueue(maxsize=10)
    
    use_mock = "--mock" in sys.argv
    
    if use_mock:
        print("Initializing Mock Radio Adapter (Local Testing)...")
        radio = MockRadioClient(frequency=10000.0)
    else:
        print("Discovering SDR nodes...")
        discovery = KiwiSDRDiscoveryService()
        nodes = discovery.fetch_nodes()
        
        if not nodes:
            print("No nodes found. Falling back to MockRadioClient for testing.")
            radio = MockRadioClient(frequency=10000.0)
        else:
            scheduler = BanditScheduler(nodes)
            best_node = scheduler.get_best_node()
            print(f"Initializing Radio Adapter on {best_node.host}:{best_node.port} (Name: {best_node.name})...")
            radio = KiwiSDRAdapter(host=best_node.host, port=best_node.port, frequency=10000.0)
    
    print("Initializing Inference Engine...")
    asr = FasterWhisperEngine(model_size="tiny", device="cpu")
    extractor = BasicFeatureExtractor()
    tuner = HillClimbingAutoTuner(initial_params={"frequency": 10000.0})
    
    # 2. Create Workers
    radio_worker = RadioWorker(radio=radio, queue=queue)
    inference_worker = InferenceWorker(asr=asr, extractor=extractor, tuner=tuner, queue=queue)
    
    # 3. Start Workers
    print("Starting workers...")
    radio_worker.start()
    inference_worker.start()
    
    try:
        while True:
            time.sleep(1)
            if not radio_worker.is_alive():
                print("[Main] RadioWorker encerrou inesperadamente.")
                if not use_mock and 'scheduler' in locals() and scheduler:
                    print(f"[Scheduler] Penalizando nó atual por queda na conexão.")
                    scheduler.update_node_score(best_node.host, best_node.port, reward=0.0)
                    
                    best_node = scheduler.get_best_node()
                    print(f"[Scheduler] Tentando próximo nó: {best_node.name} ({best_node.host}:{best_node.port})...")
                    
                    radio = KiwiSDRAdapter(host=best_node.host, port=best_node.port, frequency=10000.0)
                    radio_worker = RadioWorker(radio=radio, queue=queue)
                    radio_worker.start()
                else:
                    print("Usando mock ou sem nós disponíveis. Finalizando.")
                    break
                    
            if not inference_worker.is_alive():
                print("InferenceWorker encerrou. Finalizando...")
                break
    except KeyboardInterrupt:
        print("\nDesligando workers...")
        radio_worker.stop()
        inference_worker.stop()
        # Join pode travar se as threads estiverem bloqueadas, então damos um timeout
        radio_worker.join(timeout=2)
        inference_worker.join(timeout=2)
        print("Finalizado.")

if __name__ == "__main__":
    main()
