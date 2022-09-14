import os
import requests
import uuid
import logging

labelstudio_url = os.environ['LABEL_STUDIO_URL']
labelstudio_token = os.environ['LABEL_STUDIO_TOKEN']
labelstudio_pid = os.environ['LABEL_STUDIO_PROJECT_ID']

class LabelStudioClient:
    @staticmethod
    def upload_file(file_path):

        auth_header = {'Authorization' : 'Token {}'.format(labelstudio_token)}
        param = {'commit_to_project': 'false'}
        files = {'file': open(file_path, 'rb')}
        get_task_url = f"{labelstudio_url}/api/projects/{labelstudio_pid}/import"

        response = requests.post(get_task_url,files=files, params=param,headers=auth_header)

        if response.ok:
            logging.debug("File uploaded!")
            json_response = response.json()
            file_ids = json_response['file_upload_ids']
            file_id = None
            if file_ids is not None and len(file_ids) > 0:
                file_id = file_ids[0]
            if file_id is not None:
                get_upload_file_url = f"{labelstudio_url}/api/import/file-upload/{file_id}"
                response = requests.get(get_upload_file_url,headers=auth_header)
                if response.ok:
                    logging.debug(response.json())
                    return response.json()
                else:
                    logging.error('cant get uploaded info')
        else:
            logging.error("Error uploading file!")
        return None
    @staticmethod
    def create_task_with_file(file_path):
        resp = LabelStudioClient.upload_file(file_path)
        if resp != None:
            fileurl = '/data/' + resp['file']
            task_json = [{
                "data": {"image": fileurl},
                "annotations": [],
                "predictions": []
                }
            ]
            auth_header = {'Authorization' : f'Token {labelstudio_token}'}
            task_url = f"{labelstudio_url}/api/projects/{labelstudio_pid}/import"
            response = requests.post(task_url, json=task_json,  headers=auth_header)
            if response.ok:
                created_task = response.json()
                logging.debug(created_task)
                return True
            else:
                logging.error('Failed to create Task {}'.format(response))


if __name__ == '__main__':
    # resp = LabelStudioClient.upload_file('./img.jpg',1)
    # print(resp)
    
    resp =LabelStudioClient.create_task_with_file('./img.jpg')
    print(resp)