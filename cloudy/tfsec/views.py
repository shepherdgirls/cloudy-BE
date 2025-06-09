import os
import json
import tempfile
import subprocess

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny  

class CheckTerraformSecurityView(APIView):
    permission_classes = [AllowAny]  

    def post(self, request):
        try:
            terraform_code = request.data.get('terraform_code')

            if terraform_code is None:
                return Response({'error': 'terraform_code is missing'}, status=status.HTTP_400_BAD_REQUEST)

            with tempfile.TemporaryDirectory() as temp_dir:
                tf_path = os.path.join(temp_dir, 'main.tf')
                with open(tf_path, 'w') as f:
                    f.write(terraform_code)

                result = subprocess.run(
                    ['tfsec', temp_dir, '--format', 'json'],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE
                )

                stdout = result.stdout.decode()
                stderr = result.stderr.decode()

                if result.returncode != 0:
                    return Response({
                        'status': 'error',
                        'message': 'tfsec failed',
                        'stdout': stdout,
                        'stderr': stderr
                    })

                return Response({
                    'status': 'success',
                    'data': json.loads(stdout)  # 문자열 → JSON으로 파싱
                }, status=status.HTTP_200_OK)

        except json.JSONDecodeError:
            return Response({'error': 'Invalid JSON'}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({'error': 'Internal server error', 'detail': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
