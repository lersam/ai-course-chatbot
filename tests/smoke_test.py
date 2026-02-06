import traceback

print('\n--- Running smoke test script (smoke_test.py) ---')
ok = True
try:
    from ai_course_chatbot.ai_modules.pdf_loader import PDFLoader

    print('Imported PDFLoader')
    pl = PDFLoader()


    class FakeDoc:
        pass


    d = FakeDoc()
    d.page_content = ("This is a test. ") * 200
    d.metadata = {'source': 'fake.pdf', 'page': 1}
    chunks = pl.text_splitter.split_documents([d])
    print('Chunks:', len(chunks))
    if chunks:
        print('First chunk preview:', chunks[0].page_content[:200])
except Exception as e:
    ok = False
    print('PDFLoader test failed')
    traceback.print_exc()
try:
    import vector_store
    from ai_course_chatbot.ai_modules import rag_chatbot

    print('Imported rag_chatbot and vector_store')
except Exception as e:
    ok = False
    print('Import of rag_chatbot/vector_store failed')
    traceback.print_exc()
print('\nSMOKE-TEST-OK' if ok else '\nSMOKE-TEST-FAILED')
